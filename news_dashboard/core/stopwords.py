# -*- coding: utf-8 -*-
"""
统一停用词表

- BASE_STOP_WORDS: 基础停用词，用于索引构建和搜索查询分词
- TOPIC_STOP_WORDS: 扩展停用词（含经济/政治模板词），用于热点话题聚类
"""

BASE_STOP_WORDS = {
    # 中文基础停用词（虚词、代词、常见无实义词）
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', 
    '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', 
    '着', '没有', '看', '好', '自己', '这', '那', '这些', '那些', '这个', 
    '那个', '之', '与', '及', '或', '但', '而', '然而', '因为', '所以', 
    '因此', '如果', '即使', '虽然', '尽管', '如此', '便', '由', '被', '把', '给', '让', '向', '往', 
    '自', '从', '到', '关于', '对于', '为了', '为着', '除', '除了', '除去', '凭着', '根据', '按照', 
    '通过', '经过', '随着', '作为', '如同', '好像', '一样', '似的', '似乎', 
    '一样', '一般', '似的', '一样地', '般地',
    # 英文停用词
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
    'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 
    'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 
    'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come',
    'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well',
    'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are',
    'were', 'been', 'has', 'had', 'did', 'does', 'doing', 'done',
}

# 热点话题聚类专用扩展停用词（经济/政治新闻中的高频模板词）
_TOPIC_EXTRA_STOP_WORDS = {
    '同比', '环比', '预增', '预降', '预计', '营收', '净利润', '归母',
}

TOPIC_STOP_WORDS = BASE_STOP_WORDS | _TOPIC_EXTRA_STOP_WORDS

# 热点话题 phrase 级别子串黑名单（这些词不能出现在最终话题名称中）
TOPIC_BLOCK_WORDS = {
    '新华社', '新华网', '央视新闻', '央视网', '人民日报', '环球时报', '界面新闻', '通讯社',
    '当地时间', '北京时间', '日说', '日称', '日表示', '日回应', '暂无', '对此',
    '报道称', '据报道', '消息称', '消息人士', '知情人士',
}
