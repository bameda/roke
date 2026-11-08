#!/usr/bin/env bash
# roke-gateway: network policy and port publishing for a roke project.
#
#   roke-gateway start     set up DNS, the firewall and port forwards, then wait
#   roke-gateway blocked   list what the project tried to reach and was denied
#
# Settings (environment):
#   ROKE_NETWORK            restricted (default) or open
#   ROKE_NETWORK_ALLOW_ALL  allowed destinations, whitespace-separated:
#                           domain, *.domain, IP or CIDR, each with an
#                           optional :port (example.com:5432, 10.0.0.0/8:22),
#                           or host:PORT, a port of the host (Docker's
#                           host.docker.internal), which needs the port
#   ROKE_FORWARD_<NAME>     "LISTEN_PORT HOST:PORT": forward a gateway port to
#                           an internal service (the services publish their
#                           web UIs on the host this way)
#   ROKE_DNS_UPSTREAM       upstream resolver (default: Docker's, 127.0.0.11)
set -euo pipefail

LOG_DIR=/var/log/roke
DNS_LOG="$LOG_DIR/dns.log"
UPSTREAM="${ROKE_DNS_UPSTREAM:-127.0.0.11}"
MODE="${ROKE_NETWORK:-restricted}"

log() { printf '[roke-gateway] %s\n' "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

# set_name PORT: the nftables set for destinations allowed on PORT ("any").
set_name() { if [[ "$1" == any ]]; then echo allow_any; else echo "allow_p$1"; fi; }

start() {
  [[ "$MODE" == restricted || "$MODE" == open ]] || die "ROKE_NETWORK must be restricted or open, not '$MODE'"
  mkdir -p "$LOG_DIR"
  chown dnsmasq "$LOG_DIR"
  local dns_uid; dns_uid="$(id -u dnsmasq)"

  # Internal subnets: every connected network except the one holding the
  # default route (that one leads to the host and the internet).
  local egress_dev internal=()
  egress_dev="$(ip -4 route show default | awk '{print $5; exit}')"
  while read -r subnet _ dev _; do
    [[ "$dev" != "$egress_dev" ]] && internal+=("$subnet")
  done < <(ip -4 route show scope link | awk '{print $1, "dev", $3}')
  ((${#internal[@]})) || die "no internal network found"

  # --- Allowed destinations ----------------------------------------------------
  # Domains go to dnsmasq, which adds the addresses it resolves to the matching
  # set; IPs and CIDRs go straight into the sets.
  declare -A ports=([any]=1)
  local dns_conf=/etc/dnsmasq.d/roke.conf entry host port elems=()
  mkdir -p /etc/dnsmasq.d
  {
    echo "port=53"
    echo "listen-address=127.0.0.1"
    echo "bind-interfaces"
    echo "no-resolv"
    echo "user=dnsmasq"
    echo "filter-AAAA"
    echo "cache-size=2000"
    echo "log-queries"
    echo "log-facility=$DNS_LOG"
    echo "server=//$UPSTREAM"           # unqualified names: the project's services
    if [[ "$MODE" == open ]]; then
      echo "server=$UPSTREAM"
    else
      echo "address=/#/"                # anything not allowed: NXDOMAIN
    fi
  } > "$dns_conf"

  for entry in ${ROKE_NETWORK_ALLOW_ALL:-}; do
    port=any
    host="$entry"
    if [[ "$entry" =~ ^(.+):([0-9]+)$ ]]; then host="${BASH_REMATCH[1]}"; port="${BASH_REMATCH[2]}"; fi
    host="${host#\*.}"
    if [[ "$host" == host ]]; then
      # A port of the host, never the whole host.
      if [[ "$port" == any ]]; then
        log "WARNING: ignoring 'host' without a port; allow host:PORT"
        continue
      fi
      host="$(getent ahostsv4 host.docker.internal | awk '{print $1; exit}')"
      if [[ -z "$host" ]]; then
        log "WARNING: cannot resolve host.docker.internal; ignoring host:$port"
        continue
      fi
    fi
    ports[$port]=1
    if [[ "$host" =~ ^[0-9.]+(/[0-9]+)?$ ]]; then
      elems+=("add element inet roke $(set_name "$port") { $host }")
    elif [[ "$MODE" == restricted ]]; then
      echo "server=/$host/$UPSTREAM" >> "$dns_conf"
      echo "nftset=/$host/4#inet#roke#$(set_name "$port")" >> "$dns_conf"
    fi
  done

  # --- Firewall -------------------------------------------------------------------
  # The box shares this network namespace, so its traffic goes through the
  # output hook here; it has no capabilities to change these rules.
  local rules=/etc/roke-gateway.nft p
  {
    echo "table inet roke {"
    for p in "${!ports[@]}"; do
      echo "  set $(set_name "$p") { type ipv4_addr; flags interval; auto-merge; }"
    done
    echo "  set internal { type ipv4_addr; flags interval; elements = { $(IFS=,; echo "${internal[*]}") } }"
    echo "  set blocked { type ipv4_addr . inet_proto . inet_service; flags dynamic, timeout; timeout 1h; size 4096; }"
    # All DNS goes to the local dnsmasq, whatever resolver a program uses,
    # except dnsmasq's own upstream queries.
    echo "  chain dns { type nat hook output priority dstnat; policy accept;"
    echo "    meta skuid != $dns_uid meta l4proto { tcp, udp } th dport 53 redirect to :53"
    echo "  }"
    if [[ "$MODE" == open ]]; then
      echo "  chain output { type filter hook output priority 0; policy accept; }"
    else
      echo "  chain output { type filter hook output priority 0; policy drop;"
      # Loopback, including DNS queries redirected to dnsmasq (they keep their
      # original output interface, so match on the destination).
      echo "    ip daddr 127.0.0.0/8 accept"
      echo "    ct state established,related accept"
      echo "    ip daddr @internal accept"
      echo "    meta skuid $dns_uid ip daddr $UPSTREAM meta l4proto { tcp, udp } th dport 53 accept"
      echo "    ip daddr @allow_any accept"
      for p in "${!ports[@]}"; do
        [[ "$p" == any ]] && continue
        echo "    ip daddr @$(set_name "$p") meta l4proto { tcp, udp } th dport $p accept"
      done
      echo "    meta l4proto { tcp, udp } add @blocked { ip daddr . meta l4proto . th dport }"
      echo "    meta l4proto tcp reject with tcp reset"
      echo "    reject"
      echo "  }"
    fi
    echo "}"
    printf '%s\n' "${elems[@]}"
  } > "$rules"
  nft delete table inet roke 2>/dev/null || true
  nft -f "$rules" || die "invalid firewall rules (see $rules)"

  dnsmasq --conf-file="$dns_conf" || die "dnsmasq failed to start"

  # --- Port forwards to internal services ------------------------------------------
  local var spec
  for var in $(compgen -v ROKE_FORWARD_ || true); do
    spec="${!var}"
    read -r listen target <<<"$spec"
    [[ -n "$listen" && -n "$target" ]] || { log "WARNING: ignoring $var='$spec'"; continue; }
    socat "TCP-LISTEN:${listen},fork,reuseaddr" "TCP:${target}" &
  done

  log "network: $MODE"
  touch /run/roke-gateway.ready
  trap 'exit 0' TERM INT
  sleep infinity & wait
}

blocked() {
  echo "Domains the project looked up and were not allowed:"
  if [[ -f "$DNS_LOG" ]]; then
    grep -o 'config [^ ]* is NXDOMAIN' "$DNS_LOG" | awk '{print $2}' | sort | uniq -c | sort -rn \
      | awk '{printf "  %-50s %s lookups\n", $2, $1}' | head -50
  fi
  echo
  echo "Addresses the project tried to connect to and were not allowed (last hour):"
  nft --json list set inet roke blocked 2>/dev/null \
    | grep -o '"concat": \[[^]]*\]' | sed -E 's/"concat": \["?([^",]*)"?, "?([^",]*)"?, ([0-9]+)\]/  \1  \2 port \3/' \
    | grep -v '^  127\.' | sort -u | head -50 || true
}

case "${1:-start}" in
  start)   start ;;
  blocked) blocked ;;
  *)       die "usage: roke-gateway start|blocked" ;;
esac
