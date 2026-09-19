// The existing mix is the transport clock; stems share its seeks, rate and pauses.
export class VoiceMixer {
  constructor(master, changed, failed) {
    this.master = master;
    this.changed = changed;
    this.failed = failed;
    this.tracks = [];
    this.urls = [];
    this.enabled = [];
    master.addEventListener('playing', () => this.start());
    master.addEventListener('pause', () => this.pause());
    master.addEventListener('waiting', () => this.pause());
    master.addEventListener('ended', () => this.pause());
    master.addEventListener('seeking', () => this.pause());
    master.addEventListener('seeked', () => this.sync());
    master.addEventListener('ratechange', () => {
      for (const track of this.tracks) track.playbackRate = master.playbackRate;
      this.sync();
    });
    master.addEventListener('timeupdate', () => {
      for (const track of this.tracks) {
        if (!master.seeking && Math.abs(track.currentTime - master.currentTime) > 0.025) {
          track.currentTime = master.currentTime;
        }
      }
    });
  }
  get ready() { return this.tracks.length > 0; }
  clear() {
    for (const track of this.tracks) { track.pause(); track.removeAttribute('src'); track.load(); track.remove(); }
    for (const url of this.urls) URL.revokeObjectURL(url);
    this.tracks = []; this.urls = []; this.enabled = [];
    this.master.muted = false;
    this.changed();
  }
  load(blobs) {
    this.clear();
    this.enabled = blobs.map(() => true);
    this.tracks = blobs.map((blob, i) => {
      const track = document.createElement('audio');
      track.hidden = true; track.className = 'voice-audio'; track.dataset.voice = i;
      track.preload = 'auto'; track.playbackRate = this.master.playbackRate;
      const url = URL.createObjectURL(blob); this.urls.push(url); track.src = url;
      track.addEventListener('error', () => { if (this.tracks.includes(track)) this.fail(); });
      document.body.append(track); track.load(); return track;
    });
    this.master.muted = true;
    this.changed();
    if (!this.master.paused) this.start();
  }
  fail() { this.clear(); this.failed(); }
  toggle(i) {
    if (!this.ready) return;
    this.enabled[i] = !this.enabled[i];
    this.tracks[i].muted = !this.enabled[i];
    this.changed();
  }
  pause() { for (const track of this.tracks) track.pause(); }
  sync() {
    for (const track of this.tracks) track.currentTime = this.master.currentTime;
    if (!this.master.paused && !this.master.seeking) this.start();
  }
  start() {
    if (!this.ready || this.master.paused || this.master.seeking) return;
    const tracks = [...this.tracks];
    const time = this.master.currentTime;
    for (const track of tracks) {
      track.currentTime = time;
      track.play().catch(error => {
        if (tracks[0] === this.tracks[0] && error.name !== 'AbortError') this.fail();
      });
    }
  }
}
