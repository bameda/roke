# Disposable SSH host for testing Ansible playbooks from inside the box.
# Debian/Ubuntu based (apt). Change the base with SSH_TARGET_BASE_IMAGE.
ARG BASE_IMAGE=debian:trixie-slim
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

# python3 is required by most Ansible modules; python3-apt by the apt module.
RUN apt-get update && apt-get install -y --no-install-recommends \
      openssh-server python3 python3-apt sudo ca-certificates util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash ansible \
    && echo 'ansible ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ansible \
    && chmod 0440 /etc/sudoers.d/ansible \
    && mkdir -p /run/sshd

COPY --chmod=0755 entrypoint.sh /usr/local/bin/ssh-target-entrypoint

EXPOSE 22
HEALTHCHECK --interval=2s --timeout=3s --retries=30 \
  CMD bash -c '</dev/tcp/127.0.0.1/22' || exit 1

ENTRYPOINT ["/usr/local/bin/ssh-target-entrypoint"]
