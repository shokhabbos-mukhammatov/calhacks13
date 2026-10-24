import Architecture from "./components/Architecture";
import Fix from "./components/Fix";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import Live from "./components/Live";
import Loop from "./components/Loop";
import MathSection from "./components/MathSection";
import Nav from "./components/Nav";
import Replay from "./components/Replay";
import Results from "./components/Results";

export default function App() {
  return (
    <>
      <a className="skip" href="#drill">Skip to the drill replay</a>
      <Nav />
      <main>
        <Hero />
        <Loop />
        <Replay />
        <Fix />
        <Results />
        <MathSection />
        <Architecture />
        <Live />
      </main>
      <Footer />
    </>
  );
}
