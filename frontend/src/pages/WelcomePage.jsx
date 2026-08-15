import { Link } from "react-router-dom";

const CSS = `
.welcome {
  min-height: 100vh;
  background: #0f1420;
  color: #e8ecf4;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6rem 1.5rem 4rem;
}
.welcome-hero { text-align: center; max-width: 42rem; }
.welcome-eyebrow {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7dd3c0;
  margin-bottom: 1.25rem;
}
.welcome h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 1.1rem;
}
.welcome-sub {
  font-size: 1.1rem;
  line-height: 1.6;
  color: #aab4c8;
  margin: 0 0 2.2rem;
}
.welcome-cta-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.8rem;
}
.welcome-cta {
  display: inline-block;
  background: #7dd3c0;
  color: #0f1420;
  font-weight: 600;
  font-size: 1rem;
  padding: 0.85rem 2.2rem;
  border-radius: 999px;
  text-decoration: none;
  transition: background 0.15s ease;
}
.welcome-cta:hover { background: #9be0cf; }
.welcome-cta-alt {
  display: inline-block;
  color: #7dd3c0;
  font-size: 0.92rem;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.15s ease;
}
.welcome-cta-alt:hover { border-bottom-color: #7dd3c0; }
.welcome-note {
  margin-top: 0.9rem;
  font-size: 0.82rem;
  color: #6b7688;
}
.welcome-features {
  margin-top: 4rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  width: 100%;
  max-width: 54rem;
}
.welcome-feature {
  background: #171e2e;
  border: 1px solid #242e44;
  border-radius: 12px;
  padding: 1.25rem;
}
.welcome-feature h3 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.02rem;
  margin: 0 0 0.45rem;
  color: #f2f5fa;
}
.welcome-feature p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.55;
  color: #aab4c8;
}
.welcome-footer {
  margin-top: 4rem;
  font-size: 0.8rem;
  color: #5c6677;
}
`;

export default function WelcomePage() {
  return (
    <>
      <style>{CSS}</style>
      <main className="welcome">
        <section className="welcome-hero">
          <p className="welcome-eyebrow">Research Assistant</p>
          <h1>Ask questions across your uploaded research papers</h1>
          <p className="welcome-sub">
            Upload PDFs and ask anything — answers are grounded in the actual
            text of your papers, with the sources cited.
          </p>
          <p className="welcome-cta-row">
            <Link to="/login" className="welcome-cta">
              Get started
            </Link>
            <Link to="/login?mode=register" className="welcome-cta-alt">
              New here? Create an account
            </Link>
          </p>
          <p className="welcome-note">Already have an account? Log in — takes you to your papers.</p>
        </section>

        <section className="welcome-features">
          <div className="welcome-feature">
            <h3>Upload papers</h3>
            <p>
              Add PDFs to your library. Each paper is processed into chunks and
              indexed for searching.
            </p>
          </div>
          <div className="welcome-feature">
            <h3>Ask questions</h3>
            <p>
              Chat about your papers. Every answer is drawn from the paper text
              and shows which sources it came from.
            </p>
          </div>
          <div className="welcome-feature">
            <h3>Compare papers</h3>
            <p>
              Put papers side by side across research dimensions, and surface
              gaps in the covered literature.
            </p>
          </div>
          <div className="welcome-feature">
            <h3>Keep history</h3>
            <p>
              Past conversations stay saved, so you can return to an answer or
              line of questioning later.
            </p>
          </div>
        </section>

        <footer className="welcome-footer">
          Runs locally — your papers stay on this machine
        </footer>
      </main>
    </>
  );
}
