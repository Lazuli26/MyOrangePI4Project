Module.register("MMM-CaseMedia", {
  defaults: {
    mediaPath: "public/media",
    refreshInterval: 60000,
    recursive: true,
    randomOrder: true,
    sortBy: "name",
    imageDuration: 15000,
    videoDuration: 30000,
    videoLoop: true,
    videoMuted: true,
    fitMode: "cover",
    positionPreset: "center-center",
    objectPosition: "",
    displayMode: "background",
    shape: "rounded",
    widgetWidth: "360px",
    widgetHeight: "360px",
    cornerRadius: "24px",
    backgroundDimmer: 0,
    showEmptyState: true
  },

  start() {
    this.mediaItems = [];
    this.currentIndex = -1;
    this.currentItem = null;
    this.displayTimer = null;
    this.errorMessage = "";
    this.sendSocketNotification("MMM_CASEMEDIA_CONFIG", {
      identifier: this.identifier,
      config: this.config
    });
  },

  suspend() {
    this.clearDisplayTimer();
  },

  resume() {
    this.scheduleAdvance();
  },

  getStyles() {
    return ["MMM-CaseMedia.css"];
  },

  socketNotificationReceived(notification, payload) {
    if (!payload || payload.identifier !== this.identifier) {
      return;
    }

    if (notification === "MMM_CASEMEDIA_MEDIA_LIST") {
      this.errorMessage = "";
      this.mediaItems = payload.items || [];
      this.resetPlayback();
      return;
    }

    if (notification === "MMM_CASEMEDIA_ERROR") {
      this.errorMessage = payload.error || "Unable to load media.";
      this.mediaItems = [];
      this.currentIndex = -1;
      this.currentItem = null;
      this.clearDisplayTimer();
      this.updateDom(0);
    }
  },

  notificationReceived(notification) {
    if (notification === "MMM_CASEMEDIA_REFRESH") {
      this.sendSocketNotification("MMM_CASEMEDIA_REFRESH", {
        identifier: this.identifier
      });
    }
  },

  resetPlayback() {
    this.clearDisplayTimer();

    if (!this.mediaItems.length) {
      this.currentIndex = -1;
      this.currentItem = null;
      this.updateDom(0);
      return;
    }

    this.currentIndex = this.getNextIndex();
    this.currentItem = this.mediaItems[this.currentIndex];
    this.updateDom(300);
    this.scheduleAdvance();
  },

  getNextIndex() {
    if (!this.mediaItems.length) {
      return -1;
    }

    if (this.mediaItems.length === 1) {
      return 0;
    }

    if (this.config.randomOrder) {
      let nextIndex = this.currentIndex;
      while (nextIndex === this.currentIndex) {
        nextIndex = Math.floor(Math.random() * this.mediaItems.length);
      }
      return nextIndex;
    }

    return (this.currentIndex + 1) % this.mediaItems.length;
  },

  advanceMedia() {
    if (!this.mediaItems.length) {
      return;
    }

    this.clearDisplayTimer();
    this.currentIndex = this.getNextIndex();
    this.currentItem = this.mediaItems[this.currentIndex];
    this.updateDom(300);
    this.scheduleAdvance();
  },

  scheduleAdvance() {
    this.clearDisplayTimer();

    if (!this.currentItem) {
      return;
    }

    const duration =
      this.currentItem.type === "video"
        ? Number(this.config.videoDuration)
        : Number(this.config.imageDuration);

    if (!Number.isFinite(duration) || duration <= 0) {
      return;
    }

    this.displayTimer = setTimeout(() => {
      this.advanceMedia();
    }, duration);
  },

  clearDisplayTimer() {
    if (this.displayTimer) {
      clearTimeout(this.displayTimer);
      this.displayTimer = null;
    }
  },

  buildRootClassName() {
    const classes = ["mm-casemedia-root"];
    classes.push(
      this.config.displayMode === "background" ? "is-background" : "is-widget"
    );
    classes.push(`fit-${this.config.fitMode}`);
    classes.push(`shape-${this.config.shape}`);
    return classes.join(" ");
  },

  resolveObjectPosition() {
    const customPosition = String(this.config.objectPosition || "").trim();
    if (customPosition) {
      return customPosition;
    }

    const presets = {
      "top-left": "left top",
      "top-center": "center top",
      "top-right": "right top",
      "center-left": "left center",
      "center-center": "center center",
      "center-right": "right center",
      "bottom-left": "left bottom",
      "bottom-center": "center bottom",
      "bottom-right": "right bottom"
    };

    return presets[this.config.positionPreset] || presets["center-center"];
  },

  applySizing(wrapper) {
    wrapper.style.setProperty("--mm-casemedia-width", this.config.widgetWidth);
    wrapper.style.setProperty("--mm-casemedia-height", this.config.widgetHeight);
    wrapper.style.setProperty("--mm-casemedia-radius", this.config.cornerRadius);
    wrapper.style.setProperty(
      "--mm-casemedia-dimmer",
      String(this.config.backgroundDimmer)
    );
    wrapper.style.setProperty(
      "--mm-casemedia-position",
      this.resolveObjectPosition()
    );
  },

  createEmptyState() {
    const empty = document.createElement("div");
    empty.className = "mm-casemedia-empty";

    if (this.errorMessage) {
      empty.innerText = this.errorMessage;
      return empty;
    }

    if (this.config.showEmptyState) {
      empty.innerText =
        "Add images or videos to modules/MMM-CaseMedia/public/media";
    }

    return empty;
  },

  createMediaElement(item) {
    if (item.type === "video") {
      return this.createVideoElement(item);
    }

    const image = document.createElement("img");
    image.className = "mm-casemedia-media";
    image.src = item.url;
    image.alt = item.name || "Case media";
    image.loading = "eager";
    return image;
  },

  createVideoElement(item) {
    const video = document.createElement("video");
    const duration = Number(this.config.videoDuration);
    const useLoop = Number.isFinite(duration) && duration > 0 && this.config.videoLoop;

    video.className = "mm-casemedia-media";
    video.src = item.url;
    video.autoplay = true;
    video.muted = Boolean(this.config.videoMuted);
    video.defaultMuted = Boolean(this.config.videoMuted);
    video.loop = useLoop;
    video.controls = false;
    video.playsInline = true;
    video.preload = "auto";
    video.setAttribute("disablePictureInPicture", "true");

    if (!useLoop) {
      video.addEventListener("ended", () => {
        this.advanceMedia();
      });
    }

    return video;
  },

  getDom() {
    const wrapper = document.createElement("div");
    wrapper.className = this.buildRootClassName();
    this.applySizing(wrapper);

    const stage = document.createElement("div");
    stage.className = "mm-casemedia-stage";

    if (!this.currentItem) {
      stage.appendChild(this.createEmptyState());
      wrapper.appendChild(stage);
      return wrapper;
    }

    stage.appendChild(this.createMediaElement(this.currentItem));

    if (Number(this.config.backgroundDimmer) > 0) {
      const dimmer = document.createElement("div");
      dimmer.className = "mm-casemedia-dimmer";
      stage.appendChild(dimmer);
    }

    wrapper.appendChild(stage);
    return wrapper;
  }
});
