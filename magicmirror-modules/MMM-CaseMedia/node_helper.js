const fs = require("fs");
const path = require("path");
const NodeHelper = require("node_helper");

module.exports = NodeHelper.create({
  start() {
    this.instances = new Map();
  },

  stop() {
    for (const state of this.instances.values()) {
      if (state.refreshHandle) {
        clearInterval(state.refreshHandle);
      }
    }
    this.instances.clear();
  },

  socketNotificationReceived(notification, payload) {
    if (notification === "MMM_CASEMEDIA_CONFIG") {
      this.configureInstance(payload);
      return;
    }

    if (notification === "MMM_CASEMEDIA_REFRESH") {
      this.sendMediaList(payload.identifier);
    }
  },

  configureInstance(payload) {
    const identifier = payload.identifier;
    const config = payload.config || {};
    const mediaPath = this.resolveMediaPath(config.mediaPath);
    const state = {
      identifier,
      config,
      mediaPath,
      refreshHandle: null
    };

    this.ensureMediaDirectory(mediaPath);
    this.instances.set(identifier, state);
    this.setRefreshTimer(identifier);
    this.sendMediaList(identifier);
  },

  setRefreshTimer(identifier) {
    const state = this.instances.get(identifier);
    if (!state) {
      return;
    }

    if (state.refreshHandle) {
      clearInterval(state.refreshHandle);
      state.refreshHandle = null;
    }

    const refreshInterval = Number(state.config.refreshInterval);
    if (!Number.isFinite(refreshInterval) || refreshInterval <= 0) {
      return;
    }

    state.refreshHandle = setInterval(() => {
      this.sendMediaList(identifier);
    }, refreshInterval);
  },

  resolveMediaPath(mediaPath) {
    const relativePath = mediaPath || "public/media";
    return path.resolve(this.path, relativePath);
  },

  ensureMediaDirectory(mediaPath) {
    fs.mkdirSync(mediaPath, { recursive: true });
  },

  sendMediaList(identifier) {
    const state = this.instances.get(identifier);
    if (!state) {
      return;
    }

    try {
      const items = this.collectMediaItems(state);
      this.sendSocketNotification("MMM_CASEMEDIA_MEDIA_LIST", {
        identifier,
        items
      });
    } catch (error) {
      this.sendSocketNotification("MMM_CASEMEDIA_ERROR", {
        identifier,
        error: error.message
      });
    }
  },

  collectMediaItems(state) {
    const extensions = {
      image: new Set([".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]),
      video: new Set([".mp4", ".webm", ".mov", ".m4v"])
    };
    const files = this.walkDirectory(state.mediaPath, Boolean(state.config.recursive));
    const publicRoot = path.resolve(this.path, "public");

    return files
      .map((filePath) => {
        const ext = path.extname(filePath).toLowerCase();
        let type = "";

        if (extensions.image.has(ext)) {
          type = "image";
        } else if (extensions.video.has(ext)) {
          type = "video";
        } else {
          return null;
        }

        const relativeToPublic = path.relative(publicRoot, filePath);
        if (relativeToPublic.startsWith("..")) {
          return null;
        }

        return {
          name: path.basename(filePath),
          type,
          url: this.buildPublicUrl(relativeToPublic),
          updatedAt: fs.statSync(filePath).mtimeMs
        };
      })
      .filter(Boolean)
      .sort((left, right) => {
        if (state.config.sortBy === "modified") {
          return right.updatedAt - left.updatedAt;
        }
        return left.name.localeCompare(right.name, undefined, { numeric: true });
      });
  },

  walkDirectory(directoryPath, recursive) {
    const entries = fs.readdirSync(directoryPath, { withFileTypes: true });
    const results = [];

    for (const entry of entries) {
      if (entry.name.startsWith(".")) {
        continue;
      }

      const fullPath = path.join(directoryPath, entry.name);

      if (entry.isDirectory()) {
        if (recursive) {
          results.push(...this.walkDirectory(fullPath, recursive));
        }
        continue;
      }

      results.push(fullPath);
    }

    return results;
  },

  buildPublicUrl(relativeToPublic) {
    const normalized = relativeToPublic.split(path.sep).map(encodeURIComponent).join("/");
    return `/${this.name}/${normalized}`;
  }
});
