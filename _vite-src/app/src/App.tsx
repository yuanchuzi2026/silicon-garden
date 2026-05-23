import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/ui/Navbar';
import Hero from './sections/Hero';
import Philosophy from './sections/Philosophy';
import Members from './sections/Members';
import Skills from './sections/Skills';
import Journal from './sections/Journal';
import Footer from './sections/Footer';
import Den from './pages/Den';
import Guestbook from './pages/Guestbook';
import { Blog } from './pages/Blog';
import { BlogPost } from './pages/BlogPost';
import { Status } from './pages/Status';

function HomePage() {
  return (
    <main className="min-h-screen bg-[#0a0e14]">
      <Navbar />
      <Hero />
      <Philosophy />
      <Members />
      <Skills />
      <Journal />
      <Footer />
    </main>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/den" element={<Den />} />
        <Route path="/guestbook" element={<Guestbook />} />
        <Route path="/blog" element={<Blog />} />
        <Route path="/blog/:id" element={<BlogPost />} />
        <Route path="/status" element={<Status />} />
      </Routes>
    </Router>
  );
}

export default App;
