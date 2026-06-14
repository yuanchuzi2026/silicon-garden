import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import Home from "./pages/Home";
import Guestbook from "./pages/Guestbook";
import Awakening from "./pages/Awakening";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/guestbook" element={<Guestbook />} />
          <Route path="/awakening" element={<Awakening />} />
          <Route path="/message" element={<Guestbook />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
