/* Managed by OrangePi project automation on 2026-06-10 */
let config = {
  address: "0.0.0.0",
  port: 8080,
  ipWhitelist: [
    "127.0.0.1",
    "::ffff:127.0.0.1",
    "::1",
    "192.168.50.0/24",
    "::ffff:192.168.50.0/120"
  ],
  language: "en",
  locale: "en-US",
  timeFormat: 24,
  units: "metric",
  zoom: 1,
  modules: [
    {
      module: "alert"
    },
    {
      module: "MMM-CaseMedia",
      position: "fullscreen_below",
      config: {
        mediaPath: "public/media",
        refreshInterval: 30000,
        recursive: true,
        randomOrder: true,
        sortBy: "modified",
        imageDuration: 15000,
        videoDuration: 30000,
        videoLoop: true,
        videoMuted: true,
        fitMode: "contain",
        positionPreset: "center-center",
        objectPosition: "",
        displayMode: "background",
        shape: "rounded",
        backgroundDimmer: 0
      }
    },
    {
      module: "updatenotification",
      position: "top_bar"
    },
    {
      module: "clock",
      position: "top_left"
    },
    {
      module: "calendar",
      header: "Calendar",
      position: "top_right",
      config: {
        maximumEntries: 6,
        maximumNumberOfDays: 30
      }
    },
    {
      module: "compliments",
      position: "lower_third"
    },
    {
      module: "newsfeed",
      position: "bottom_bar",
      config: {
        feeds: [
          {
            title: "BBC World",
            url: "https://feeds.bbci.co.uk/news/world/rss.xml"
          }
        ],
        showSourceTitle: true,
        showPublishDate: true,
        broadcastNewsFeeds: true,
        broadcastNewsUpdates: true
      }
    },
    {
      module: "MMM-Remote-Control",
      config: {
        apiKey: "2b10fe8cd073a15ea1900508c59d845e",
        secureEndpoints: true,
        showModuleApiMenu: true
      }
    }
  ]
};

if (typeof module !== "undefined") {
  module.exports = config;
}
