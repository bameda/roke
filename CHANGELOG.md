# Changelog

Each release lists its commits, grouped by type, with migration notes for
breaking changes.

## [0.1.0] - 2026-11-10

<!-- roke-release-base: 6f6f5869b4359faae811b66a4aae26e777e24bc6 -->

### Breaking changes

- feat(postgres)!: default to PostgreSQL 18 with its new data layout ([056e6103](https://github.com/bameda/roke/commit/056e6103d7d6d20231dead42324151b118afd0a5))
  the postgres service now requires PostgreSQL 18 or newer,
  and its volume is renamed from postgres-data to pgdata, so existing
  projects start with an empty database.
- refactor(services)!: use one directory per service ([44ab3348](https://github.com/bameda/roke/commit/44ab33489940011ac681476d161934a25087b627))
  custom services must move from services/<name>.yaml to
  services/<name>/compose.yaml.
- feat!: keep personal configuration outside the repository ([866de55b](https://github.com/bameda/roke/commit/866de55b93f8809f582433004469ef79563e5d84))
  move .env to ~/.config/ocbox/ocbox.env, projects/* to
  ~/.config/ocbox/projects/ and config/opencode/* to
  ~/.config/ocbox/opencode/, then run `ocbox --init` to add the missing files.
- feat!: give each project its own configuration directory ([e3a2f07f](https://github.com/bameda/roke/commit/e3a2f07f9bff6a6823bd9f186ecd48d63bdb48ad))
  move projects/<name>.env to projects/<name>/project.env and
  projects/<name>.yaml to projects/<name>/compose.yaml.
- refactor!: rename the box's compose service from opencode to box ([3dc980a2](https://github.com/bameda/roke/commit/3dc980a240f71b0f23e84437b4df575ebe8a9867))
  in your own service and project compose files, rename the
  "opencode" service to "box" (for example in depends_on and environment
  overrides), and use box:<port> instead of opencode:<port> as upstream.
- feat!: support several coding agents: Claude Code and OpenCode ([4151758e](https://github.com/bameda/roke/commit/4151758e8763150bff2776aa48f9376cb4694811))
  choose an agent with `ocbox --default-agent claude|opencode`.
  Move ~/.config/ocbox/opencode/AGENTS.md to ~/.config/ocbox/AGENTS.md and
  the rest of ~/.config/ocbox/opencode/ to ~/.config/ocbox/agents/opencode/,
  replace OPENCODE_VERSION with OCBOX_AGENT_VERSIONS="opencode=...", and
  rebuild the image.
- refactor!: rename the project to roke ([4d6ba85d](https://github.com/bameda/roke/commit/4d6ba85d49f13c85ff2cca94098fcf3e524a809b))
  everything named after ocbox changes:
  - the command: ocbox -> roke (rerun install.sh to link it);
  - the configuration directory: ~/.config/ocbox -> ~/.config/roke, and
    ocbox.env -> roke.env inside it;
  - every setting: OCBOX_* -> ROKE_*;
  - the box's home volume: ocbox-home -> roke-home, the image: ocbox -> roke,
    and the compose projects: ocbox-<name>-<hash> -> roke-<name>-<hash>.
- feat!: give each project its own home, shared with nothing else ([4eff4f5e](https://github.com/bameda/roke/commit/4eff4f5ed7092168b4c9eec0fbe88bfa6b3d4c55))
  the shared roke-home volume is no longer used. Log in to
  the agent again in each project (or put an API key in secrets.env), and
  remove the old volume with `docker volume rm roke-home`.
- feat!: restrict the project's network to allowed destinations by default ([d6ead748](https://github.com/bameda/roke/commit/d6ead748f60391ba76032aafac409cb9a986dae7))
  projects can only reach allowed destinations unless
  ROKE_NETWORK=open. Services can no longer publish ports themselves: in
  your own compose files, replace "ports:" on a service with a
  ROKE_FORWARD_<NAME> and a "ports:" entry on the gateway (see
  services/README.md). Rebuild the images with roke --build.
- feat(services)!: replace MinIO with RustFS, and add Prometheus and Grafana ([77a4b017](https://github.com/bameda/roke/commit/77a4b0172823390416edffbc92bc1bf4cc1d8fc2))
  the minio service is gone: use rustfs instead in
  ROKE_SERVICES, and rename MINIO_* settings to RUSTFS_* (MINIO_USER and
  MINIO_PASSWORD become RUSTFS_ACCESS_KEY and RUSTFS_SECRET_KEY). Data in
  existing minio volumes is not migrated.
- feat!: turn roke's actions into subcommands ([dc215692](https://github.com/bameda/roke/commit/dc215692407ab3046d4398543df2dbe254f7f364))
  the action flags are gone. roke --down becomes roke down,
  --build becomes roke build (which no longer starts the agent),
  --rebuild becomes roke build --no-cache, -c becomes roke continue,
  --shell becomes roke shell, -- CMD becomes roke exec CMD, --list becomes
  roke agent and roke service, --settings and --urls become roke settings
  and roke urls, --blocked and --allow become roke network blocked and
  roke network add, --set-agent NAME and --default-agent NAME become
  roke agent use NAME [--global], --set-agent default becomes
  roke agent reset, --init and --update become roke init and roke update,
  and the project directory is given with -C DIR.
- fix(security)!: never import roke from the current directory ([842845fa](https://github.com/bameda/roke/commit/842845fa4f2ddb78056b8579820cb562a311d574))
  roke no longer reads PYTHONPATH or other PYTHON*
  variables; nothing in roke relied on them.
- refactor!: move agents/, services/ and mcps/ into catalog/ ([3a7b46d4](https://github.com/bameda/roke/commit/3a7b46d4bdf3aa96113d7d3cbb664e031f324990))
  a compose.yaml of yours that refers to a catalog file by
  its path in roke's repository must add catalog/ to it, for example
  ./services/ssh-target becomes ./catalog/services/ssh-target, as in the
  ansible example project.
- feat!: add stable project IDs with automatic adoption ([c4f0af96](https://github.com/bameda/roke/commit/c4f0af96f96802e0aec24afcc86bdb88d44c344b))
  Projects with colliding directory names need distinct IDs. Choose one with roke --id NAME and register existing projects before moving their directories.
- feat!: simplify project identity and settings commands ([1789a6f9](https://github.com/bameda/roke/commit/1789a6f9f50116eb1bc8f9074884f30775da5a96))
  --id is limited to builds and session starts. Use roke settings show ID to inspect another project's settings.
- feat!: isolate box images by build configuration ([a35e368f](https://github.com/bameda/roke/commit/a35e368f458057165d61258b91ff955df12d335a))
  Run roke build once per build configuration to create tagged box variants. Existing project IDs and volumes are retained.
- feat!: clarify Docker versions in YAML diagnostics ([6333561b](https://github.com/bameda/roke/commit/6333561b75a3400204904071a1553db3a8e43e55))
  consumers of doctor YAML must use versions.docker_compose instead of versions.compose.
- feat!: add stable and main update channels ([ace3ecf5](https://github.com/bameda/roke/commit/ace3ecf5b7534368fb27796660db8e538d42fd62))
  New installations default to stable releases. Set ROKE_VERSION=main to install from main before the first stable release. Update custom
    development branches manually with Git.

### Features

- feat: initial release of opencode-box ([4b6f1b57](https://github.com/bameda/roke/commit/4b6f1b57dfa98b751eb24e7c5eb6536e4072f4e7))
- feat(postgres)!: default to PostgreSQL 18 with its new data layout ([056e6103](https://github.com/bameda/roke/commit/056e6103d7d6d20231dead42324151b118afd0a5))
- feat(services): add ssh-target service for testing Ansible playbooks ([d8414870](https://github.com/bameda/roke/commit/d84148701f372e80948af61520ea9879b1706659))
- feat!: keep personal configuration outside the repository ([866de55b](https://github.com/bameda/roke/commit/866de55b93f8809f582433004469ef79563e5d84))
- feat: clone the configuration from a private repository on install ([262d6995](https://github.com/bameda/roke/commit/262d699562e03cb6cf98723455838e178ae31567))
- feat!: give each project its own configuration directory ([e3a2f07f](https://github.com/bameda/roke/commit/e3a2f07f9bff6a6823bd9f186ecd48d63bdb48ad))
- feat(image): add kcat and build dependencies for native extensions ([39293550](https://github.com/bameda/roke/commit/39293550f7bbd88ff04c29730d8adecf6da0b53e))
- feat(services): add kwok, registry, nats, kafka, jaeger and wiremock ([60887cf5](https://github.com/bameda/roke/commit/60887cf5bce0b1c40260aa7b39ed1ab68d0c67dd))
- feat!: support several coding agents: Claude Code and OpenCode ([4151758e](https://github.com/bameda/roke/commit/4151758e8763150bff2776aa48f9376cb4694811))
- feat!: give each project its own home, shared with nothing else ([4eff4f5e](https://github.com/bameda/roke/commit/4eff4f5ed7092168b4c9eec0fbe88bfa6b3d4c55))
- feat!: restrict the project's network to allowed destinations by default ([d6ead748](https://github.com/bameda/roke/commit/d6ead748f60391ba76032aafac409cb9a986dae7))
- feat: show the project's settings with roke --settings ([9cc64e68](https://github.com/bameda/roke/commit/9cc64e686034cd27ab519a987e3b3089a4ed668f))
- feat: group roke's options and add --continue to resume the last session ([ae660f1b](https://github.com/bameda/roke/commit/ae660f1bde5dee5be7bfb216e60401c3e705c98a))
- feat(agents): add Codex CLI ([892c3b47](https://github.com/bameda/roke/commit/892c3b474f9a9abc1ca6811745d85d51dea71e7c))
- feat: install roke with a single command, and add roke --update ([aa8a4dcb](https://github.com/bameda/roke/commit/aa8a4dcb6eded214e4ad274d75281865df19979f))
- feat(services)!: replace MinIO with RustFS, and add Prometheus and Grafana ([77a4b017](https://github.com/bameda/roke/commit/77a4b0172823390416edffbc92bc1bf4cc1d8fc2))
- feat(services): add SeaweedFS as an alternative S3-compatible store ([fc859da2](https://github.com/bameda/roke/commit/fc859da2ccbe99069322bf1b05e8dd2a5a1c6599))
- feat: show where the project's services and ports are with roke --urls ([d809c5be](https://github.com/bameda/roke/commit/d809c5bec90dcde75e805da7cc91b70bba037d10))
- feat!: turn roke's actions into subcommands ([dc215692](https://github.com/bameda/roke/commit/dc215692407ab3046d4398543df2dbe254f7f364))
- feat: pin service versions per project, and add roke service upgrade ([bf0d400d](https://github.com/bameda/roke/commit/bf0d400d3607f9ec75b54514531edc89f45a5397))
- feat: show one variable and one destination per line ([a09fe64c](https://github.com/bameda/roke/commit/a09fe64c2f0361c9730c3a9434fe67c26eae43e5))
- feat: sort the allowed destinations alphabetically in roke network ([9aa8fe89](https://github.com/bameda/roke/commit/9aa8fe89a1b98b1de98b4ecbacca46d97c9f15fa))
- feat: manage MCP servers like services, for any agent ([e161a11d](https://github.com/bameda/roke/commit/e161a11df360c62b2fbae8a24eff7036407a4570))
- feat(mcps): add Penpot's hosted MCP server ([873ea2d0](https://github.com/bameda/roke/commit/873ea2d0e5bd328fdb526191a0974b13daf268b9))
- feat: run several agents in a project at once, without cutting each other off ([e93b6d51](https://github.com/bameda/roke/commit/e93b6d516b3f7752c834d11dca46ab45025864c0))
- feat: edit the settings, show catalog entries, and one question per command ([c9cd772d](https://github.com/bameda/roke/commit/c9cd772d7fab49542e542bbe34ee7b268f509816))
- feat(services): add an OpenLDAP for tests ([6f6ee502](https://github.com/bameda/roke/commit/6f6ee502a149237fea6b56a3566a28bdfda2d4ee))
- feat(network): allow a port of the host, one at a time ([02edc413](https://github.com/bameda/roke/commit/02edc413b3539384f6970b66712bfd9a70a02356))
- feat: render the READMEs of the show commands for the terminal ([b0f12316](https://github.com/bameda/roke/commit/b0f12316bbc369cf4cd9eb41b1f3ef2db958fc9c))
- feat: turn off Serena's usage statistics, and mark known blocked lookups ([adb190ee](https://github.com/bameda/roke/commit/adb190ee2f76edca9d8fbd8a78a8fd3e06cdffdb))
- feat(codex): turn off Codex's own sandbox, and trust the project ([79fef281](https://github.com/bameda/roke/commit/79fef281a688dd3ac1485a21768289de01fe24d3))
- feat: tell the agent about the restricted network ([23957a8b](https://github.com/bameda/roke/commit/23957a8bd38a89b6844683a04ae96c07d68b483a))
- feat(network): say what each allowed destination is for ([6cf8dd62](https://github.com/bameda/roke/commit/6cf8dd620390be83c44d6145179d781c311fa98e))
- feat(network): suggest a note when allowing a destination ([76d9b385](https://github.com/bameda/roke/commit/76d9b3852e475fcd3452af71467e6d4f6ce554ce))
- feat(services): add playwright, browsers the box cannot run ([c554140f](https://github.com/bameda/roke/commit/c554140f2df14e03fe41dbbb5ca87015cbb8ab64))
- feat: add project diagnostics command ([3a486614](https://github.com/bameda/roke/commit/3a4866147ce14945f0693df1a4482dceb0bdf25f))
- feat: add project logs with service discovery ([9e85964a](https://github.com/bameda/roke/commit/9e85964a5aa992c8102762d75b61e5a5c28dd2ad))
- feat!: add stable project IDs with automatic adoption ([c4f0af96](https://github.com/bameda/roke/commit/c4f0af96f96802e0aec24afcc86bdb88d44c344b))
- feat!: simplify project identity and settings commands ([1789a6f9](https://github.com/bameda/roke/commit/1789a6f9f50116eb1bc8f9074884f30775da5a96))
- feat!: isolate box images by build configuration ([a35e368f](https://github.com/bameda/roke/commit/a35e368f458057165d61258b91ff955df12d335a))
- feat: add YAML diagnostics to bug reports ([e979a5e3](https://github.com/bameda/roke/commit/e979a5e309d5257ce94e1b5400a4aa73ff12d494))
- feat!: clarify Docker versions in YAML diagnostics ([6333561b](https://github.com/bameda/roke/commit/6333561b75a3400204904071a1553db3a8e43e55))
- feat: accept multiple ports in a single port option ([4502f491](https://github.com/bameda/roke/commit/4502f4916f87d077320d76d31d1424c7ff5ea10e))
- feat: show actual published ports and Compose identity ([53338d1b](https://github.com/bameda/roke/commit/53338d1bcd979feb84a7a402b09ccea80c19b9e8))
- feat: expose application version in CLI and diagnostics ([c831ef3a](https://github.com/bameda/roke/commit/c831ef3a5215e24c9801d160507ab8f5920adf33))
- feat!: add stable and main update channels ([ace3ecf5](https://github.com/bameda/roke/commit/ace3ecf5b7534368fb27796660db8e538d42fd62))
- feat: automate release preparation and publication ([6f6f5869](https://github.com/bameda/roke/commit/6f6f5869b4359faae811b66a4aae26e777e24bc6))

### Fixes

- fix(mariadb): make the mariadb/mysql client work without arguments ([44eaa265](https://github.com/bameda/roke/commit/44eaa2656ff234a5cfe18e7489480db6e4caac1c))
- fix(rabbitmq): pin the hostname so data survives container recreation ([baf4ef57](https://github.com/bameda/roke/commit/baf4ef5778460639f659e589949e6086027b5315))
- fix(gateway): build when the dnsmasq user already exists ([920ab659](https://github.com/bameda/roke/commit/920ab6596166ecc0f9aba14c377766e4a2c3e283))
- fix: show the whole help with roke --help, and agent, service and network --help ([1d827579](https://github.com/bameda/roke/commit/1d827579d779ca9f301c2261883f2002428c6b20))
- fix(security)!: never import roke from the current directory ([842845fa](https://github.com/bameda/roke/commit/842845fa4f2ddb78056b8579820cb562a311d574))
- fix: point the catalog lists to roke ... show ([851ce09d](https://github.com/bameda/roke/commit/851ce09d29527626b3d65a7aa0aa93bf39b7bb5e))
- fix(network): allow Sigstore's trust root, which mise needs to verify tools ([66a4609c](https://github.com/bameda/roke/commit/66a4609ce4423d698fae463bec4aa706306b90d0))
- fix: validate MCP definitions and network destinations ([14998ccf](https://github.com/bameda/roke/commit/14998ccfbe9fd698d116f1cba4e16ae4be88d56c))
- fix: report settings and Compose failures clearly ([652e9cdb](https://github.com/bameda/roke/commit/652e9cdb0a9439cd4bc3bb1cefa206eb1d49b1d8))
- fix: validate network destinations from all sources ([a008be8d](https://github.com/bameda/roke/commit/a008be8d2f469b142f5645205cfd4ddbfcf61a5b))
- fix: propagate Docker query and shutdown failures ([50c37e76](https://github.com/bameda/roke/commit/50c37e76ad49586f3e60941fc36106c79fff20fc))

### Documentation

- docs: add first steps guide ([91bc7bd9](https://github.com/bameda/roke/commit/91bc7bd96504630222a6275a855951ff16bb6ce0))
- docs(services): add a usage guide to every service ([0638ea70](https://github.com/bameda/roke/commit/0638ea703df32fde6e198142108204859ed18fd1))
- docs(readme): add install steps per distribution and the repository URL ([1b6862a3](https://github.com/bameda/roke/commit/1b6862a3a68cc893f4a23ab4766e4de0c7dd8245))
- docs: reorganize the documentation into a short README and topic guides ([11951dcd](https://github.com/bameda/roke/commit/11951dcd05f58d20a4c09f2bab2d0d4eb0f0784e))
- docs(examples): add example projects for Ansible, Python, Node.js and Clojure ([8b6e79aa](https://github.com/bameda/roke/commit/8b6e79aa275728c282f2408ae1810d3a2484ceb6))
- docs(examples): add Helm, Go, Rust, Rails and Spring Boot example projects ([df23c26f](https://github.com/bameda/roke/commit/df23c26f66cf2a67d4a1b13bf50dba2fe44c8fed))
- docs(readme): open with the origin of the name ([ee513fb4](https://github.com/bameda/roke/commit/ee513fb4d679dd32742542b54a4f84db64c765d6))
- docs: add a contributing guide, a security policy, and issue and PR templates ([0e335905](https://github.com/bameda/roke/commit/0e335905c8c4886b4980066398c3e7f10587dc98))
- docs: adopt the Contributor Covenant 3.0, with a clause on reverse discrimination ([a3962fec](https://github.com/bameda/roke/commit/a3962fecf2c306515306fa9c5c775790955458b4))
- docs: add a contact email for conduct and security reports ([f3155b2b](https://github.com/bameda/roke/commit/f3155b2b92edb3fdab1eca04f2912140b8788be6))
- docs: add AGENTS.md, for contributors working with coding agents ([42906c28](https://github.com/bameda/roke/commit/42906c287aa4def1289268d65ad6b426dcd50091))
- docs(examples): add Penpot, with its own development environment ([502b2163](https://github.com/bameda/roke/commit/502b2163df60ee473e9c480d0508123336c12792))
- docs: copy the examples from the installation, not ~/src/roke ([620dfe2f](https://github.com/bameda/roke/commit/620dfe2f56d4019b8b86f6bea68998b84a2a7eb6))
- docs: clarify runtime flow and rebuild requirements ([c5bcf26f](https://github.com/bameda/roke/commit/c5bcf26f8cf9495dfe7e67c020351e5ecded6f80))
- docs: simplify first project setup ([9049a221](https://github.com/bameda/roke/commit/9049a221663fb71b51ae6232834ac54dbbd029d9))

### Tests

- test: add a test suite for roke, and run it in GitHub Actions ([e105b0cf](https://github.com/bameda/roke/commit/e105b0cfd78d6991403985fd2985867d1784c7aa))
- test: keep the tests independent of branches and of the catalog's versions ([4a21e90c](https://github.com/bameda/roke/commit/4a21e90c29dca794c548deb4959d69be25903752))
- test: add Docker integration coverage in CI ([7586ee73](https://github.com/bameda/roke/commit/7586ee7336887cfefb2aae9cefa4aa58db4200eb))
- test: fail CI on missing prerequisites and unexpected skips ([5570d3ec](https://github.com/bameda/roke/commit/5570d3ece5f5bb9225648af1e7b645998f76e293))

### Refactoring

- refactor(services)!: use one directory per service ([44ab3348](https://github.com/bameda/roke/commit/44ab33489940011ac681476d161934a25087b627))
- refactor!: rename the box's compose service from opencode to box ([3dc980a2](https://github.com/bameda/roke/commit/3dc980a240f71b0f23e84437b4df575ebe8a9867))
- refactor!: rename the project to roke ([4d6ba85d](https://github.com/bameda/roke/commit/4d6ba85d49f13c85ff2cca94098fcf3e524a809b))
- refactor: rewrite the roke command in Python ([91611318](https://github.com/bameda/roke/commit/91611318737d3ae8a2656b0bf26e940167e1a1f7))
- refactor: group the agents and services catalogs in roke/catalog ([5de6c465](https://github.com/bameda/roke/commit/5de6c465b2e7b0b0bc8e788a2e13373e5624c41e))
- refactor: group the presentation code in roke/ui ([b3a8862d](https://github.com/bameda/roke/commit/b3a8862da931bd774e3a1a3408c87aff30945298))
- refactor!: move agents/, services/ and mcps/ into catalog/ ([3a7b46d4](https://github.com/bameda/roke/commit/3a7b46d4bdf3aa96113d7d3cbb664e031f324990))
- refactor: make doctor checks actionable ([1cbf5054](https://github.com/bameda/roke/commit/1cbf5054ca80957ca43081f87be7e793f2087556))

### Build and dependencies

- build: update dependencies with Renovate, keeping each version in one place ([646fb951](https://github.com/bameda/roke/commit/646fb9516d30c35339fcbcd056b2e1f0b95f3a84))

### Maintenance

- chore: add MIT license ([5b4a406d](https://github.com/bameda/roke/commit/5b4a406dc756fe83fc04618dbb755ab0564ea6d6))
- chore: add development tooling with pre-commit ([03cf89dd](https://github.com/bameda/roke/commit/03cf89dd07405b18239804b7eb76cd902df0583b))
- chore(deps): update valkey/valkey docker tag to v9 ([8a71f1a8](https://github.com/bameda/roke/commit/8a71f1a82b99f6a4fd37c019d4dfeb0a2bc70fef))
- chore(deps): update redis docker tag to v8 ([5127a28b](https://github.com/bameda/roke/commit/5127a28b65db3cba545e703e7093d514ecf1ac07))
- chore(deps): update mongo docker tag to v9 ([e4489c50](https://github.com/bameda/roke/commit/e4489c503df1e0db46f87ac6b3e82549d391f2d1))
- chore(deps): update mariadb docker tag to v13 ([f5a2e6ba](https://github.com/bameda/roke/commit/f5a2e6ba2c5026afaafc8e067d061d261849967f))
- chore(deps): update docker.elastic.co/elasticsearch/elasticsearch docker tag to v9 ([bdf8c612](https://github.com/bameda/roke/commit/bdf8c612820ebe031d59eeff899b1089f01e124b))
- chore(deps): update docker.redpanda.com/redpandadata/redpanda docker tag to v26.2.6 ([ac7f6338](https://github.com/bameda/roke/commit/ac7f6338cc10941ff68dbdbb0efd02fad13f337a))
- chore(deps): update axllent/mailpit docker tag to v1.33.1 ([f1642b8b](https://github.com/bameda/roke/commit/f1642b8b89c14950b1d78cc82bdf176b15c355c4))
- chore(deps): update chrislusf/seaweedfs docker tag to v4.53 ([58725030](https://github.com/bameda/roke/commit/587250302c7969ac0964c68482379b32a03a5fc4))

[All commits](https://github.com/bameda/roke/commits/v0.1.0)
