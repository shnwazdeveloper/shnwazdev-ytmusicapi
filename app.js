const AUTO_REFRESH_MS = 60000;

const elements = {
  controls: document.querySelector("#controls"),
  country: document.querySelector("#country"),
  search: document.querySelector("#search"),
  refresh: document.querySelector("#refresh"),
  status: document.querySelector("#status"),
  songCount: document.querySelector("#song-count"),
  regionLabel: document.querySelector("#region-label"),
  updatedAt: document.querySelector("#updated-at"),
  playlistId: document.querySelector("#playlist-id"),
  nowTitle: document.querySelector("#now-title"),
  nowArtists: document.querySelector("#now-artists"),
  nowCover: document.querySelector("#now-cover"),
  listenLink: document.querySelector("#listen-link"),
  list: document.querySelector("#song-list"),
  empty: document.querySelector("#empty-state"),
  resultNote: document.querySelector("#result-note"),
  template: document.querySelector("#song-template"),
};

const state = {
  songs: [],
  payload: null,
  refreshTimer: 0,
  request: null,
};

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

function getSearchTerm() {
  return elements.search.value.trim().toLowerCase();
}

function getThumbnail(song) {
  const thumbnails = Array.isArray(song.thumbnails) ? song.thumbnails : [];
  if (!thumbnails.length) {
    return "";
  }

  return [...thumbnails].sort((a, b) => (b.width || 0) - (a.width || 0))[0]?.url || "";
}

function getVisibleSongs() {
  const term = getSearchTerm();
  if (!term) {
    return state.songs;
  }

  return state.songs.filter((song) => {
    const target = `${song.title || ""} ${song.artistsText || ""}`.toLowerCase();
    return target.includes(term);
  });
}

function setLoading(isLoading) {
  document.documentElement.classList.toggle("is-loading", isLoading);
  elements.refresh.disabled = isLoading;
}

function setStatus(text) {
  elements.status.textContent = text;
}

function renderHero(song) {
  const hasSong = Boolean(song);
  const cover = hasSong ? getThumbnail(song) : "";

  elements.nowTitle.textContent = hasSong ? song.title : "Realtime YouTube Music Trending Songs";
  elements.nowArtists.textContent = hasSong ? song.artistsText || "YouTube Music" : "Loading live songs...";
  elements.listenLink.href = hasSong && song.youtubeMusicUrl ? song.youtubeMusicUrl : "https://music.youtube.com";
  elements.listenLink.setAttribute("aria-disabled", hasSong ? "false" : "true");

  elements.nowCover.classList.toggle("has-art", Boolean(cover));
  if (cover) {
    elements.nowCover.src = cover;
  } else {
    elements.nowCover.removeAttribute("src");
  }
}

function renderStats(payload) {
  const updated = payload?.updatedAt ? new Date(payload.updatedAt) : null;

  elements.songCount.textContent = payload ? String(payload.count) : "--";
  elements.regionLabel.textContent = payload?.countryLabel || "--";
  elements.updatedAt.textContent = updated && !Number.isNaN(updated.valueOf()) ? dateFormatter.format(updated) : "--";
  elements.playlistId.textContent = payload?.playlist ? payload.playlist.replace(/^VL/, "") : "--";
}

function renderSongs() {
  const songs = getVisibleSongs();
  const fragment = document.createDocumentFragment();

  elements.list.textContent = "";
  elements.empty.hidden = songs.length > 0;
  elements.resultNote.textContent = state.payload
    ? `${songs.length} of ${state.payload.count} songs`
    : "Fresh from YouTube Music";

  songs.forEach((song, index) => {
    const item = elements.template.content.firstElementChild.cloneNode(true);
    const cover = getThumbnail(song);
    const link = item.querySelector(".song-link");
    const image = item.querySelector(".song-cover");

    item.style.animationDelay = `${Math.min(index * 32, 360)}ms`;
    item.querySelector(".rank").textContent = String(song.rank).padStart(2, "0");
    item.querySelector("h3").textContent = song.title || "Untitled";
    item.querySelector("p").textContent = song.artistsText || "YouTube Music";
    item.querySelector(".views").textContent = song.views || "Live";
    link.href = song.youtubeMusicUrl || song.youtubeUrl || "https://music.youtube.com";
    image.alt = song.title ? `${song.title} cover` : "";

    if (cover) {
      image.src = cover;
    } else {
      image.removeAttribute("src");
    }

    fragment.appendChild(item);
  });

  elements.list.appendChild(fragment);
}

function render(payload) {
  state.payload = payload;
  state.songs = Array.isArray(payload.items) ? payload.items : [];

  renderHero(state.songs[0]);
  renderStats(payload);
  renderSongs();
}

function scheduleRefresh() {
  window.clearTimeout(state.refreshTimer);
  state.refreshTimer = window.setTimeout(() => {
    if (!document.hidden) {
      loadTrending({ silent: true });
    }
  }, AUTO_REFRESH_MS);
}

async function loadTrending({ silent = false } = {}) {
  if (state.request) {
    state.request.abort();
  }

  const controller = new AbortController();
  state.request = controller;
  const params = new URLSearchParams({
    country: elements.country.value,
    t: String(Date.now()),
  });

  if (!silent) {
    setStatus("Loading");
  }
  setLoading(true);

  try {
    const response = await fetch(`/api/trending?${params.toString()}`, {
      cache: "no-store",
      signal: controller.signal,
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Request failed");
    }

    render(payload);
    setStatus("Live");
    scheduleRefresh();
  } catch (error) {
    if (error.name === "AbortError") {
      return;
    }

    setStatus("Unavailable");
    elements.resultNote.textContent = error.message;
    elements.empty.hidden = false;
    elements.empty.textContent = "Trending songs are not available right now.";
  } finally {
    if (state.request === controller) {
      setLoading(false);
      state.request = null;
    }
  }
}

elements.controls.addEventListener("submit", (event) => {
  event.preventDefault();
  loadTrending();
});

elements.country.addEventListener("change", () => loadTrending());
elements.search.addEventListener("input", renderSongs);

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && state.payload) {
    loadTrending({ silent: true });
  }
});

loadTrending();
