/**
 * 网站详情页 (About)
 * 地球在中间，信息分布在左右两边
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Database, Globe, Server, Code, Zap, Clock, Newspaper } from 'lucide-react';
import Earth3D from '../components/Earth3D';

export default function About() {
  const navigate = useNavigate();
  
  // 返回主页
  const handleBack = () => {
    navigate('/');
  };
  
  // 技术栈数据
  const techStack = [
    { name: 'Flask', icon: <Server size={20} />, desc: 'Python Web 框架', color: '#00d4ff' },
    { name: 'MySQL', icon: <Database size={20} />, desc: '关系型数据库', color: '#f1c40f' },
    { name: 'React', icon: <Code size={20} />, desc: '前端框架', color: '#00d4ff' },
    { name: 'Three.js', icon: <Globe size={20} />, desc: '3D 图形库', color: '#e74c3c' },
    { name: 'Tailwind CSS', icon: <Zap size={20} />, desc: 'CSS 框架', color: '#2ecc71' },
    { name: 'Framer Motion', icon: <Clock size={20} />, desc: '动画库', color: '#9b59b6' },
  ];
  
  // 新闻源数据
  const newsSources = [
    { name: 'Reuters', logo: 'R', color: '#ff6b00' },
    { name: 'BBC', logo: 'B', color: '#bb1919' },
    { name: '新华网', logo: 'X', color: '#c41e3a' },
    { name: 'Associated Press', logo: 'AP', color: '#ff0000' },
    { name: '财新网', logo: 'C', color: '#1a5276' },
    { name: '澎湃新闻', logo: 'P', color: '#000000' },
    { name: 'TechCrunch', logo: 'TC', color: '#0a9e01' },
    { name: 'The Verge', logo: 'V', color: '#e2127a' },
  ];
  
  // 功能特性
  const features = [
    { 
      icon: <Globe size={24} />, 
      title: '全球覆盖', 
      desc: '支持 190+ 国家和地区的新闻数据' 
    },
    { 
      icon: <Zap size={24} />, 
      title: '实时更新', 
      desc: '48小时滚动新闻，实时倒排索引' 
    },
    { 
      icon: <Database size={24} />, 
      title: 'XML 检索', 
      desc: '支持 XPath 限定的高级搜索' 
    },
    { 
      icon: <Newspaper size={24} />, 
      title: '多源聚合', 
      desc: '整合全球主流新闻媒体' 
    },
  ];
  
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#0a0a0f]">
      {/* 左侧信息面板 */}
      <motion.div
        className="absolute left-0 top-0 w-[30%] h-full z-10 overflow-y-auto custom-scrollbar"
        initial={{ x: '-100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="h-full p-6">
          {/* 项目标题 */}
          <motion.div 
            className="mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <h1 className="font-['Orbitron'] text-3xl text-white mb-2">
              <span className="text-[#00d4ff]">Quick</span>News
            </h1>
            <p className="text-white/60">XML 检索系统</p>
            <div className="mt-3 flex items-center gap-3">
              <span className="px-3 py-1 rounded-full bg-[#00d4ff]/20 text-[#00d4ff] text-sm">
                v1.0.0
              </span>
            </div>
          </motion.div>
          
          {/* 功能特性 */}
          <motion.section 
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            <h2 className="text-white/80 font-medium mb-4 flex items-center gap-2">
              <Zap size={20} className="text-[#00d4ff]" />
              核心功能
            </h2>
            <div className="space-y-3">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  className="glass p-3 rounded-xl"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.1, duration: 0.3 }}
                >
                  <div className="text-[#00d4ff] mb-1">{feature.icon}</div>
                  <h3 className="text-white font-medium text-sm mb-1">{feature.title}</h3>
                  <p className="text-white/50 text-xs">{feature.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.section>
          
          {/* 返回按钮 */}
          <motion.div 
            className="mt-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.4 }}
          >
            <motion.button
              onClick={handleBack}
              className="flex items-center gap-2 px-4 py-2 glass rounded-full text-white/80 hover:text-white transition-all"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <ArrowLeft size={20} />
              <span>返回主页</span>
            </motion.button>
          </motion.div>
        </div>
      </motion.div>
      
      {/* 中间地球 - 从主页过渡，略微缩小后稳定 */}
      <motion.div 
        className="absolute left-[30%] top-0 w-[40%] h-full z-[1] overflow-hidden"
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
      >
        <Earth3D
          mode="background"
          rotationSpeed={0.0003}
          enableControls={false}
          cameraPosition={[0, 0, 16]}
        />
      </motion.div>
      
      {/* 右侧信息面板 */}
      <motion.div
        className="absolute right-0 top-0 w-[30%] h-full z-10 overflow-y-auto custom-scrollbar"
        initial={{ x: '100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="h-full p-6">
          {/* 技术栈 */}
          <motion.section 
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            <h2 className="text-white/80 font-medium mb-4 flex items-center gap-2">
              <Code size={20} className="text-[#00d4ff]" />
              技术栈
            </h2>
            <div className="space-y-3">
              {techStack.map((tech, index) => (
                <motion.div
                  key={tech.name}
                  className="flex items-center gap-3 px-3 py-2 glass rounded-xl"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.05, duration: 0.3 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <span style={{ color: tech.color }}>{tech.icon}</span>
                  <div>
                    <div className="text-white font-medium text-sm">{tech.name}</div>
                    <div className="text-white/40 text-xs">{tech.desc}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.section>
          
          {/* 新闻源 */}
          <motion.section 
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.4 }}
          >
            <h2 className="text-white/80 font-medium mb-4 flex items-center gap-2">
              <Newspaper size={20} className="text-[#00d4ff]" />
              新闻数据源
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {newsSources.map((source, index) => (
                <motion.div
                  key={source.name}
                  className="glass p-2 rounded-lg text-center cursor-pointer transition-all hover:bg-white/10"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.8 + index * 0.05, duration: 0.3 }}
                  whileHover={{ scale: 1.05 }}
                >
                  <div 
                    className="w-8 h-8 rounded-full mx-auto mb-1 flex items-center justify-center text-white text-xs font-bold"
                    style={{ backgroundColor: source.color }}
                  >
                    {source.logo}
                  </div>
                  <div className="text-white/70 text-xs">{source.name}</div>
                </motion.div>
              ))}
            </div>
          </motion.section>
          
          {/* 数据说明 */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.4 }}
          >
            <h2 className="text-white/80 font-medium mb-4 flex items-center gap-2">
              <Database size={20} className="text-[#00d4ff]" />
              数据说明
            </h2>
            <div className="glass p-4 rounded-xl space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-white/60">数据保留时间</span>
                <span className="text-[#00d4ff]">48 小时</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60">更新频率</span>
                <span className="text-[#00d4ff]">实时</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60">索引类型</span>
                <span className="text-[#00d4ff]">倒排索引</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60">支持语言</span>
                <span className="text-[#00d4ff]">中文 / 英文</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60">检索协议</span>
                <span className="text-[#00d4ff]">SRU / XML</span>
              </div>
            </div>
          </motion.section>
          
          {/* 版权信息 */}
          <motion.div 
            className="mt-6 text-center text-white/30 text-xs"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.4 }}
          >
            <p>© 2024 QuickNews. All rights reserved.</p>
            <p className="mt-1">Powered by Flask + MySQL + React + Three.js</p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
