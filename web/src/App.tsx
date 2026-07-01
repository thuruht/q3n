import { useEffect, useState } from "react";
import "./App.css";

const REPO = "https://github.com/thuruht/q3n";
const RAW_SPEC = `${REPO}/blob/main/docs/format/specification.md`;

const BANNER = `\
     ###########################################################################################################################################
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
   #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
  #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
  #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
  #++++++++++++++++++++--------++++++++++++=-------+++++++++++++-------++++++++++++++--------+++++++++++-------------++++++--------++++-------++++#
  #+++++++++++++++++++.@@@@@@@@-++++++++++:@@@@@@@@-++++++++++-.@@@@@@@*++++++++++==:@@@@@@@@-==+++++++.@@@@@@@@@@@@@.++++-@@@@@@@@.++-@@@@@@@-+++#
  #+++++++++++++++++-.@@@@@@@@.++++++++++.@@@@@@@@@-+++++++++.@@@@@@@@@-+++++++++-###=@@@@@@@@+@:+++++-@@@@@@@@@@@@@@@.+++.@@@@@@@@@-+:@@@@@@@-+++#
  #++++++++++++++++:@@@@@@@@@.+++++++++--@@@@@@@@.-+++++++++-@@@@@@@@@.+++++++++=@@@@@@@@@@@@@@@@=+++=-@@@@@@@@@@@@@@@@.+-@@@@@@@@@@-=@@@@@@@@-+++#
  #+++++++++++++++:@......@@:+++++++++.@......@@.+++++++++-=-.....-@.-+++++++++--:...............--+=@:::::::::::......@-+.........+-+-.....@.++++#
  #+++++++++++++--@@@@@@@@.-++++++++=.@@@@@@@@#:+++++++++.@@@@@@@@@.++++++++++-@@@@@@@@@@@@@@@@@@@@-+-@@@@@@@@@@@@@@@@@@-:@@@@@@@@@@@.@@@@@@@-++++#
  #++++++++++++-@@@@@@@@@.+++++++++:@@@@@@@@@.=++++++++--@@@@@@@@--+++++++++++=@@@@@@@.----.@@@@@@@-++==========:@@@@@@@.@@@@@@@@@@@@@@@@@@@.+++++#
  #++++++++++-*+----..@.-+++++++++-@:----.@@.+++++++++:@-----.@@.++++++++++++++----.@.+++++-:::::.@-++++-+*++++++----.@.=-----.----.@.----.@-+++++#
  #+++++++++.@.----.@@.+++++++++-=-.----=@.-+++++++++:@.----.@@:+++++++++++++%----.@*:----.@+###**@-+++.@.----------.@.-@.---.@.---:@:---.@.++++++#
  #+++++++=-@@@@@@@@@:+++++++++-@@@@@@@@@.+++++++++-#@@@@@@@@.=++++++++++++++-@@@@@@.@@@@@@@@@@@@@.+++-@@@@@@@@@@@@@@@-.@@@@@@@@@@@@@@@@@@@-++++++#
  #++++++:@=----.@@.=++++++++-++----..@=-+++++++++-@-----.@@.++++++++++++++++@-----:@:---------.@@--+++------.@.----.@.@.---.@-@.-------.@=+++++++#
  #+++++.@.----.@@.+++++++++.@.----.@@.+++++++++---.----:@:-++++++++++++++++++=-----:---------.@@..@.---------.-----:@:.----.@.@.-------.@-+++++++#
  #+++-=@@@@@@@@.-+++++++++-@@@@@@@@@.+++++++++:@@@@@@@@@.+++++++++++++++++++=@@@@@@@@@@@@@@@@@@..@@@@@@@@@@@@@@@@@@@.@@@@@@@@-.@@@@@@@@@@-+++++++#
  #++.@......@@.+++++++++-=-.....-@.-+++++++++:@......@@:+++++++++++++++++++++=.@.:......----.@.:@.................@@:......@.++........@.++++++++#
  #+-@@@@@@@@*:+++++++++-@@@@@@@@@.++++++++++#@@@@@@@@.=++++++++++++++++++++++++-=@@@@@@@:----.@@@@@@@@@@@@@@@@@@@@::@@@@@@@@-+-@@@@@@@@@-++++++++#
  #++--------=+++++++++++---------++++++++++++--------++++++++++++++++++++++++++++=-----:@@@@@@@.-----------------=++=-------+++---------+++++++++#
  #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=------++++++++++++++++++++++++++++++++++++++++++++++++++#
  #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
   #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
   ##+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++##
     ###########################################################################################################################################`;

type PackageFile = { name: string; size: number; url: string; uploaded: string };
type Release = { tag_name: string; assets: { name: string; browser_download_url: string }[] };

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function matchFile(files: PackageFile[], ...exts: string[]): PackageFile | undefined {
  return files.find((f) => exts.some((e) => f.name.endsWith(e)));
}

type DownloadCardProps = {
  icon: string;
  title: string;
  subtitle: string;
  file?: PackageFile;
  comingSoon?: boolean;
  fallbackHref?: string;
};

function DownloadCard({ icon, title, subtitle, file, comingSoon, fallbackHref }: DownloadCardProps) {
  return (
    <div className={`card ${comingSoon ? "card--soon" : ""}`}>
      <span className="card__icon">{icon}</span>
      <div className="card__body">
        <h3 className="card__title">{title}</h3>
        <p className="card__sub">{subtitle}</p>
        {file && <span className="card__size">{formatBytes(file.size)}</span>}
      </div>
      {comingSoon ? (
        <span className="btn btn--soon">Coming soon</span>
      ) : file ? (
        <a className="btn" href={file.url} download={file.name}>
          Download
        </a>
      ) : (
        <a className="btn btn--gh" href={fallbackHref ?? `${REPO}/releases`}>
          Releases ↗
        </a>
      )}
    </div>
  );
}

export default function App() {
  const [files, setFiles] = useState<PackageFile[]>([]);
  const [version, setVersion] = useState("");
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/api/packages").then((r) => r.json()) as Promise<{ files: PackageFile[] }>,
      fetch("/api/releases").then((r) => r.json()) as Promise<Release>,
    ])
      .then(([pkgs, rel]) => {
        setFiles(pkgs.files ?? []);
        setVersion(rel.tag_name ?? "");
      })
      .catch(() => setError(true));
  }, []);

  const deb = matchFile(files, ".deb");
  const tar = matchFile(files, ".tar.gz", ".tar.xz");
  const appimg = matchFile(files, ".AppImage");

  return (
    <div className="page">
      <header className="hero">
        <pre className="hero__banner" aria-hidden="true">{BANNER}</pre>
        <h1 className="hero__title">
          <span className="hero__slash">///</span> Q3N
        </h1>
        <p className="hero__tagline">Quote Triple-Slash Notation</p>
        <p className="hero__desc">
          A plain-text format and toolchain for storing quotations with source
          URIs. Parse, search, and export your quotes from the CLI or GUI.
        </p>
        <div className="hero__links">
          <a className="hero__link" href={REPO}>GitHub</a>
          <a className="hero__link" href={RAW_SPEC}>Format spec</a>
          <a className="hero__link hero__link--accent" href="/demo.html">Try it live →</a>
        </div>
        {version && <p className="hero__version">Latest release: {version}</p>}
      </header>

      <main className="main">
        {/* ── Overview ───────────────────────────────────── */}
        <section>
          <h2 className="section-title">Overview</h2>
          <p className="section-desc">
            Q3N is a lightweight, machine-readable format for storing quotations
            with their source information. It uses triple-slash delimiters and
            URI-formatted source references.
          </p>
          <div className="features">
            <div className="feature">
              <h3 className="feature__title">URI-based Sources</h3>
              <p className="feature__body">
                Standard schemes like <code>https://</code> or custom ones like{" "}
                <code>isbn://</code>, <code>doi://</code>, <code>osm://</code>, and more.
              </p>
            </div>
            <div className="feature">
              <h3 className="feature__title">Tag Hierarchy</h3>
              <p className="feature__body">
                Organise entries with slash-delimited tags:{" "}
                <code>cite/article</code>, <code>note/idea</code>, <code>cite/book</code>.
              </p>
            </div>
            <div className="feature">
              <h3 className="feature__title">Simple Parsing</h3>
              <p className="feature__body">
                Line-by-line format parseable in any language. Implementations in
                Python and JavaScript.
              </p>
            </div>
          </div>
        </section>

        {/* ── Examples ───────────────────────────────────── */}
        <section>
          <h2 className="section-title">Examples</h2>
          <div className="examples">
            <div className="example">
              <h3 className="example__label">Web citation</h3>
              <pre className="codeblock">{`/// https://example.com/article /// cite/article:
The quoted text goes here.
\\\\\\`}</pre>
            </div>
            <div className="example">
              <h3 className="example__label">Book quote</h3>
              <pre className="codeblock">{`/// isbn://9780547249643;'1984';'George Orwell';1949
War is peace. Freedom is slavery.
\\\\\\`}</pre>
            </div>
            <div className="example">
              <h3 className="example__label">Academic paper</h3>
              <pre className="codeblock">{`/// doi://10.1126/science.187.4176.433
The more the universe seems comprehensible…
\\\\\\`}</pre>
            </div>
            <div className="example">
              <h3 className="example__label">Map location</h3>
              <pre className="codeblock">{`/// geo:51.5,-0.1?z=15 /// place:
Observed at this location.
\\\\\\`}</pre>
            </div>
          </div>
        </section>

        {/* ── Download ───────────────────────────────────── */}
        <section>
          <h2 className="section-title">Download</h2>

          {error && (
            <p className="notice">
              Could not load package info —{" "}
              <a href={`${REPO}/releases`}>see GitHub Releases</a> instead.
            </p>
          )}

          <div className="cards">
            <DownloadCard
              icon="📦"
              title="Debian / Ubuntu"
              subtitle=".deb package — installs CLI, GUI, man page, and MIME type"
              file={deb}
              fallbackHref={`${REPO}/releases`}
            />
            <DownloadCard
              icon="🗜️"
              title="Generic Linux"
              subtitle="tar.gz archive — extract anywhere, no install needed"
              file={tar}
              fallbackHref={`${REPO}/releases`}
            />
            <DownloadCard
              icon="🖥️"
              title="AppImage"
              subtitle="Portable single-file executable, runs on any x86-64 Linux"
              file={appimg}
              fallbackHref={`${REPO}/releases`}
            />
            <DownloadCard
              icon="📦"
              title="Flatpak"
              subtitle="Sandboxed, universal Linux package via Flathub"
              comingSoon
            />
          </div>
        </section>

        {/* ── Tools ──────────────────────────────────────── */}
        <section>
          <h2 className="section-title">Tools</h2>
          <div className="cards">
            <div className="card">
              <span className="card__icon">⌨️</span>
              <div className="card__body">
                <h3 className="card__title">CLI</h3>
                <p className="card__sub">
                  <code>q3n show · search · export · cite · validate</code>
                </p>
              </div>
              <a className="btn" href={REPO}>View on GitHub</a>
            </div>
            <div className="card">
              <span className="card__icon">🖼️</span>
              <div className="card__body">
                <h3 className="card__title">GUI</h3>
                <p className="card__sub">PySide6 browser and editor with plugin panels</p>
              </div>
              <a className="btn" href={REPO}>View on GitHub</a>
            </div>
            <div className="card">
              <span className="card__icon">🌐</span>
              <div className="card__body">
                <h3 className="card__title">JavaScript Parser</h3>
                <p className="card__sub">Works in Node.js and the browser</p>
              </div>
              <a className="btn" href="/demo.html">Live demo</a>
            </div>
            <div className="card">
              <span className="card__icon">🔤</span>
              <div className="card__body">
                <h3 className="card__title">VS Code Extension</h3>
                <p className="card__sub">Syntax highlighting for <code>.q3n</code> files</p>
              </div>
              <a className="btn" href={`${REPO}/tree/main/vscode-extension`}>View source</a>
            </div>
          </div>
        </section>

        {/* ── Getting Started ────────────────────────────── */}
        <section>
          <h2 className="section-title">Getting Started</h2>
          <pre className="codeblock">{`pip install q3n
q3n show examples/sample.q3n
q3n search "cosmos" .
q3n export quotes.q3n -o quotes.md -f md
q3n cite quotes.q3n --style mla --all`}</pre>
          <p className="format__desc" style={{ marginTop: "0.75rem" }}>
            Or clone and run without installing:{" "}
            <code>git clone https://github.com/thuruht/q3n && cd q3n && python tools/q3n --help</code>
          </p>
        </section>

        {/* ── Format ─────────────────────────────────────── */}
        <section className="format">
          <h2 className="section-title">The format</h2>
          <pre className="codeblock">{`#!q3n-format

/// https://example.com/article /// cite/article:
Quoted text here.
Multiple lines OK.
\\\\\\

/// isbn://978-0-13-468599-1;Title;Author;1999
No tag is fine too.
\\\\\\`}</pre>
          <p className="format__desc">
            One block per quotation. Open with <code>/// &lt;uri&gt;</code>, close with{" "}
            <code>\\\</code>. Supported schemes:{" "}
            <code>https · isbn · doi · arxiv · pubmed · orcid · spotify · yt · file · q3n · osm · geo · overpass · wikipedia · github</code>.{" "}
            <a href={RAW_SPEC}>Full specification ↗</a>
          </p>
        </section>
      </main>

      <footer className="footer">
        <img src="/favicon.png" alt="Q3N" className="footer__logo" />
        <p>
          Q3N is free software — AGPL-3.0 with Anti-Fascist Exception.{" "}
          <a href={REPO}>thuruht/q3n</a>
        </p>
      </footer>
    </div>
  );
}
