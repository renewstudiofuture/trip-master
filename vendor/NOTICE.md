# Third-party notices

scripts/xhs-extract.js contains a modified search-card extraction algorithm from:
- nashsu/AutoCLI, v0.3.8, adapters/xiaohongshu/search.yaml
- Upstream attribution: jackwener/OpenCLI, original author jackwener
- License: Apache-2.0 (licenses/AutoCLI-Apache-2.0.txt)
- Upstream NOTICE retained in AutoCLI-NOTICE.txt

Modifications: remove CLI/daemon/extension dependency; require UI sort evidence; preserve unknown likes; normalize displayed counts; deduplicate note IDs; separate private signed URLs from public links. No AutoCLI binaries or browser extension bundled. Other original Trip Master files retain their existing license.
