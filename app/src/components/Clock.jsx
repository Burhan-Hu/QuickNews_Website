/**
 * 实时数字时钟组件
 * 显示当前时区时间，带发光效果
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function Clock({ className = '' }) {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    // 每秒更新一次
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);
  
  // 格式化时间
  const formatTime = (date) => {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return { hours, minutes, seconds };
  };
  
  // 格式化日期
  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[date.getDay()];
    return `${year}年${month}月${day}日 ${weekday}`;
  };
  
  const { hours, minutes, seconds } = formatTime(time);
  
  return (
    <motion.div 
      className={`flex flex-col items-center ${className}`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
    >
      {/* 时间显示 */}
      <div className="flex items-baseline font-['Orbitron'] text-[#00d4ff] glow-text-blue">
        <motion.span 
          className="text-5xl md:text-6xl font-bold tracking-wider"
          key={hours}
          initial={{ opacity: 0.8 }}
          animate={{ opacity: 1 }}
        >
          {hours}
        </motion.span>
        <span className="text-4xl md:text-5xl mx-2 animate-pulse">:</span>
        <motion.span 
          className="text-5xl md:text-6xl font-bold tracking-wider"
          key={minutes}
          initial={{ opacity: 0.8 }}
          animate={{ opacity: 1 }}
        >
          {minutes}
        </motion.span>
        <span className="text-4xl md:text-5xl mx-2 animate-pulse">:</span>
        <motion.span 
          className="text-4xl md:text-5xl font-semibold tracking-wider text-[#00d4ff]/80"
          key={seconds}
          initial={{ opacity: 0.5, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.1 }}
        >
          {seconds}
        </motion.span>
      </div>
      
      {/* 日期显示 */}
      <motion.div 
        className="mt-2 text-white/60 text-sm md:text-base font-['Inter'] tracking-wide"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        {formatDate(time)}
      </motion.div>
      
      {/* 时区显示 */}
      <motion.div 
        className="mt-1 text-[#00d4ff]/40 text-xs font-['Inter']"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.5 }}
      >
        {Intl.DateTimeFormat().resolvedOptions().timeZone}
      </motion.div>
    </motion.div>
  );
}
