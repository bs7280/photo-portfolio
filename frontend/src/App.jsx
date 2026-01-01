import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom';
import { EditModeProvider, useEditMode } from './context/EditModeContext';
import DeployButton from './components/DeployButton';
import SyncButton from './components/SyncButton';
import Home from './pages/Home';
import Albums from './pages/Albums';
import AlbumDetail from './pages/AlbumDetail';
import './App.css';

function Navigation() {
  const { editMode } = useEditMode();

  return (
    <nav className="nav">
      <div className="nav-content">
        <Link to="/" className="nav-brand">
          Photography Portfolio
        </Link>
        <div className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            All Photos
          </NavLink>
          <NavLink to="/albums" className={({ isActive }) => isActive ? 'active' : ''}>
            Albums
          </NavLink>
          {editMode && (
            <>
              <SyncButton />
              <DeployButton />
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <EditModeProvider>
      <Router>
        <div className="app">
          <Navigation />

          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/albums" element={<Albums />} />
              <Route path="/albums/:albumId" element={<AlbumDetail />} />
            </Routes>
          </main>
        </div>
      </Router>
    </EditModeProvider>
  );
}

export default App;
