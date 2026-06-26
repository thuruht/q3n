import { useEffect, useState } from "react";
import "./App.css";

const REPO = "https://github.com/thuruht/q3n";
const RAW_SPEC = `${REPO}/blob/main/docs/format/specification.md`;

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
    // Fetch R2 package list and latest release tag in parallel
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
        </div>
        {version && <p className="hero__version">Latest release: {version}</p>}
      </header>

      <main className="main">
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
            <code>https · isbn · doi · arxiv · pubmed · orcid · spotify · yt · file · q3n</code>.
          </p>
        </section>
      </main>

      <footer className="footer">
        <p>
          Q3N is free software, MIT licensed.{" "}
          <a href={REPO}>thuruht/q3n</a>
        </p>
      </footer>
    </div>
  );
}
