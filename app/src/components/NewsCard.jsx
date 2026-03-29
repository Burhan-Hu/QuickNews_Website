/**
 * 新闻卡片组件
 * 显示新闻标题、摘要、国家标签和时间
 */

import React from 'react';
import { motion } from 'framer-motion';
import { getCountryInfo } from '../utils/countryCoords';

export default function NewsCard({
  title,
  summary,
  country,
  time,
  onClick,
  index = 0,
}) {
  // 获取国家信息
  const countryInfo = country ? getCountryInfo(country) : null;
  
  // 格式化时间
  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    try {
      const date = new Date(timeStr);
      return date.toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return timeStr;
    }
  };
  
  return (
    <motion.div
      className="card-glass cursor-pointer"
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.4, 
        delay: index * 0.05,
        ease: [0.4, 0, 0.2, 1] 
      }}
      whileHover={{ 
        scale: 1.02,
        borderColor: 'rgba(0, 212, 255, 0.3)',
      }}
    >
      {/* 标题 */}
      <h3 className="text-white font-medium text-base leading-snug mb-2 line-clamp-2">
        {title}
      </h3>
      
      {/* 摘要 */}
      {summary && (
        <p className="text-white/60 text-sm leading-relaxed mb-3 line-clamp-2">
          {summary}
        </p>
      )}
      
      {/* 元信息 */}
      <div className="flex items-center justify-between text-xs">
        {/* 国家标签 */}
        {countryInfo && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-white/5 text-white/70">
            <span>{countryInfo.emoji}</span>
            <span>{countryInfo.name}</span>
          </span>
        )}
        
        {/* 时间 */}
        {time && (
          <span className="text-white/40">
            {formatTime(time)}
          </span>
        )}
      </div>
    </motion.div>
  );
}
