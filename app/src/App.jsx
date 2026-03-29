/**
 * QuickNews 3D 新闻可视化系统 - 主应用
 * 
 * 技术栈: React 18 + Three.js + Tailwind CSS + Framer Motion
 * 功能: 3D 地球新闻可视化、XML 检索、热力图展示
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StarBackground from './components/StarBackground';
import Home from './pages/Home';
import Visual from './pages/Visual';
import Search from './pages/Search';
import About from './pages/About';

function App() {
  return (
    <Router>
      {/* 全局星空背景 */}
      <StarBackground />
      
      {/* 路由配置 */}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/visual" element={<Visual />} />
        <Route path="/search" element={<Search />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Router>
  );
}

export default App;
