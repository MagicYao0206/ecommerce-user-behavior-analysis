import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
import os
from textwrap import wrap   # 新增文本换行工具
from llama_cpp import Llama # 导入Llama相关库
from translate import Translator

warnings.filterwarnings("ignore")

# -------------------------- PDF导出核心（ReportLab版，支持中文） --------------------------
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# 注册系统宋体（Windows内置，无需复制文件）
def register_chinese_font():
    # 宋体路径（Windows系统默认路径）
    font_path = "C:\\Windows\\Fonts\\simsun.ttc"
    if os.path.exists(font_path):
        # 注册宋体，别名"SimSun"
        pdfmetrics.registerFont(TTFont("SimSun", font_path))
        return True
    else:
        st.error("未找到宋体字体文件，请检查：C:\\Windows\\Fonts\\simsun.ttc")
        return False

# 生成PDF报告
def generate_chinese_pdf(
    start_date, end_date, total_users, total_pv, total_buy, conversion,
    funnel_order, funnel_values, segment_counts, buy_peak, ai_analysis,
    top_categories, user_retention
):
    # 注册中文字体
    if not register_chinese_font():
        return None
    
    # 保存路径（自动创建文件夹）
    save_path = r"F:\ecommerce-user-behavior-analysis\results\电商用户分析报告.pdf"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 创建PDF画布（A4尺寸）
    c = canvas.Canvas(save_path, pagesize=A4)
    page_width, page_height = A4
    
    # -------------------------- 绘制PDF内容 --------------------------
    # 1. 标题（居中）
    c.setFont("SimSun", 18)  # 使用注册的宋体
    c.drawCentredString(page_width/2, page_height - 2*cm, "电商用户行为分析报告")
    
    # 2. 基本信息
    c.setFont("SimSun", 12)
    y_pos = page_height - 4*cm  # 起始Y坐标（从顶部往下4cm）
    line_height = 18  # 行高
    
    c.drawString(2*cm, y_pos, f"分析时段：{start_date} 至 {end_date}")
    y_pos -= line_height
    c.drawString(2*cm, y_pos, f"总独立用户数：{total_users:,} 人")
    y_pos -= line_height
    c.drawString(2*cm, y_pos, f"总浏览量（PV）：{total_pv:,} 次")
    y_pos -= line_height
    c.drawString(2*cm, y_pos, f"总购买量：{total_buy:,} 次")
    y_pos -= line_height
    c.drawString(2*cm, y_pos, f"整体转化率：{conversion:.2f}%")
    y_pos -= line_height
    c.drawString(2*cm, y_pos, f"用户次日留存率：{user_retention:.2f}%")
    
    # 3. 转化漏斗数据
    y_pos -= line_height * 2  # 空两行
    c.setFont("SimSun", 14)
    c.drawString(2*cm, y_pos, "一、转化漏斗分析")
    y_pos -= line_height
    c.setFont("SimSun", 12)
    
    for i, step in enumerate(funnel_order):
        c.drawString(2.5*cm, y_pos, f"{step}：{funnel_values[i]} 人")
        if i > 0:
            rate = (funnel_values[i] / funnel_values[i-1]) * 100
            c.drawString(3*cm, y_pos - line_height, f"→ 转化率：{rate:.2f}%")
            y_pos -= line_height
        y_pos -= line_height
    
    # 4. 用户分群数据
    y_pos -= line_height * 2
    c.setFont("SimSun", 14)
    c.drawString(2*cm, y_pos, "二、RFM用户分群分布")
    y_pos -= line_height
    c.setFont("SimSun", 12)
    
    for seg, cnt in segment_counts.items():
        ratio = (cnt / segment_counts.sum()) * 100
        c.drawString(2.5*cm, y_pos, f"{seg}：{cnt} 人（占比 {ratio:.1f}%）")
        y_pos -= line_height
    
    # 5. 热销品类
    y_pos -= line_height * 2
    c.setFont("SimSun", 14)
    c.drawString(2*cm, y_pos, "三、热销品类TOP3")
    y_pos -= line_height
    c.setFont("SimSun", 12)
    for i, category in enumerate(top_categories, 1):
        c.drawString(2.5*cm, y_pos, f"第{i}名：品类ID {category}")
        y_pos -= line_height

    # 6. AI分析建议
    y_pos -= line_height * 2
    c.setFont("SimSun", 14)
    c.drawString(2*cm, y_pos, "四、AI生成分析建议")
    y_pos -= line_height
    c.setFont("SimSun", 12)
    
    # 处理AI分析内容自动换行
    ai_lines = []
    for line in ai_analysis.split('\n'):
        wrapped = wrap(line, width=30, break_long_words=False)  # 按30字换行
        ai_lines.extend(wrapped)
    
    for line in ai_lines:
        if y_pos < 3*cm:  # 页底预留空间
            c.showPage()  # 新建页面
            y_pos = page_height - 3*cm  # 新页面起始位置
            c.setFont("SimSun", 12)
        c.drawString(2.5*cm, y_pos, line)
        y_pos -= line_height
    
    # 7. 页脚（页码）
    c.setFont("SimSun", 10)
    c.drawCentredString(page_width/2, 2*cm, f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 保存PDF
    c.save()
    return save_path

# -------------------------- 纯CPU版Llama模型调用 --------------------------
def load_llama_model(model_path):
    """加载本地Llama模型"""
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,        # 上下文窗口大小
            n_threads=16,      # 拉满CPU线程（i7-10870H是16线程）
            n_gpu_layers=0,    # 强制关闭GPU（纯CPU运行）
            verbose=False      # 关闭冗余日志，减少卡顿
        )
        return llm
    except Exception as e:
        st.error(f"模型加载失败：{str(e)}")
        return None

def calculate_retention(df):
    """计算用户次日留存率"""
    if df.empty:
        return 0.0
    
    # 提取用户首次行为日期和后续行为日期
    user_first_date = df.groupby("user_id")["date"].min()
    user_dates = df.groupby("user_id")["date"].unique()
    
    # 计算留存用户数
    retained = 0
    total = len(user_first_date)
    
    for user_id, first_date in user_first_date.items():
        next_day = (pd.to_datetime(first_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if next_day in user_dates[user_id]:
            retained += 1
    
    return (retained / total) * 100 if total > 0 else 0.0

def generate_ai_analysis(llm, metrics, df_filtered):
    """使用Llama生成增强版分析建议"""
    if not llm:
        return "AI分析：模型未加载，无法生成分析内容"
    
    # 提取额外分析维度
    top_categories = df_filtered[df_filtered["behavior_type"]=="buy"]["category_id"].value_counts().head(3).index.tolist()
    user_retention = calculate_retention(df_filtered)
    
    # 计算转化漏斗各环节转化率
    funnel_conversion = []
    for i in range(1, len(metrics['funnel_values'])):
        if metrics['funnel_values'][i-1] == 0:
            funnel_conversion.append(0.0)
        else:
            funnel_conversion.append(round((metrics['funnel_values'][i]/metrics['funnel_values'][i-1])*100, 2))
    funnel_steps = ["浏览→收藏", "收藏→加购", "加购→购买"]
    funnel_conversion_str = " | ".join([f"{step}：{rate}%" for step, rate in zip(funnel_steps, funnel_conversion)])

    prompt = f"""<s>[INST]
    你是专业的电商数据分析师，需基于以下数据生成结构化分析建议，严格遵守输出规则：

    ### 分析数据
    1. 分析时段：{metrics['start_date']} 至 {metrics['end_date']}
    2. 核心指标：总用户{metrics['total_users']}人 | 总浏览量{metrics['total_pv']}次 | 总购买量{metrics['total_buy']}次 | 整体转化率{metrics['conversion']:.2f}%
    3. 转化漏斗：浏览({metrics['funnel_values'][0]}人)→收藏({metrics['funnel_values'][1]}人)→加购({metrics['funnel_values'][2]}人)→购买({metrics['funnel_values'][3]}人)
       各环节转化率：{funnel_conversion_str}
    4. 购买高峰时段：{metrics['buy_peak']}点 | 热销品类TOP3：{top_categories}
    5. 高价值用户占比：{metrics['high_value_ratio']:.1f}% | 用户次日留存率：{user_retention:.2f}%

    ### 输出规则（必须严格遵守，否则分析无效）
    1. 使用中文回答；
    2. 仅输出Markdown格式的分析内容，禁止输出任何指令、说明、格式要求类文本；
    3. 内容分为「关键洞察」和「运营建议」两大模块，模块用### 标题，子项用1./- 开头；
    4. 关键洞察需结合具体数据，指出核心问题/特征，拒绝空泛描述；
    5. 运营建议需具象化、可落地，每个建议必须包含「具体动作+预期效果」，拒绝套话；
    6. 语言简洁，每个子项不超过2句话，整体字数控制在300字以内；
    7. 禁止出现英文、表情符号，仅用中文+数据+标点；
    8. 若输出中出现任何英文，将被视为无效分析，必须完全使用中文表达。

    ### 输出模板（必须按此结构填充内容）
    ### 关键洞察
    1. 转化环节：[结合转化率数据指出核心流失环节+具体数据支撑]
    2. 时段特征：[结合购买高峰指出用户行为规律+具体数据支撑]
    3. 用户结构：[结合高价值用户占比指出用户分层问题+具体数据支撑]
    4. 留存表现：[结合次日留存率指出留存问题+具体数据支撑]

    ### 运营建议
    - 转化优化：[针对核心流失环节的具体动作（如优惠券/流程优化）+ 预期提升效果]
    - 时段运营：[针对购买高峰的具体动作（如定时推送/限时活动）+ 预期提升效果]
    - 用户维护：[针对高价值用户的具体动作（如会员体系/专属权益）+ 预期提升效果]
    - 留存提升：[针对留存率的具体动作（如复购提醒/新人福利）+ 预期提升效果]
    [/INST]"""
    
    try:
        output = llm.create_completion(
            prompt=prompt,
            max_tokens=1000,  # 足够容纳结构化内容
            temperature=0.3,  # 降低随机性，保证格式严格
            top_p=0.8,        # 控制生成多样性，避免重复
            stop=["</s>"],    # 精准截断模型输出，避免多余内容
            echo=False        # 禁止回显Prompt内容
        )
        # 清理输出（移除可能的多余空格/换行）
        ai_text = output["choices"][0]["text"].strip()

        # 检测英文并翻译
        def contains_english(text):
            return any(char.isalpha() and char.isascii() for char in text)
        
        if contains_english(ai_text):
            # 初始化翻译器（英文→中文）
            translator = Translator(from_lang="en", to_lang="zh")
            # 分段落翻译（避免长文本翻译失败）
            translated_paragraphs = []
            for para in ai_text.split('\n'):
                if para.strip():  # 跳过空行
                    try:
                        translated = translator.translate(para)
                        translated_paragraphs.append(translated)
                    except:
                        translated_paragraphs.append(para)  # 翻译失败时保留原文
            ai_text = '\n'.join(translated_paragraphs)
        
        return ai_text if ai_text else "AI分析：未生成有效内容，请刷新重试"
    except Exception as e:
        return f"AI分析生成失败：{str(e)}"

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(page_title="电商用户行为分析看板", layout="wide")
# 解决matplotlib中文显示（使用系统字体）
plt.rcParams["font.sans-serif"] = ["SimSun", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# -------------------------- MySQL数据库连接 --------------------------
def get_mysql_engine():
    MYSQL_CONFIG = {
        "user": "root",
        "password": "1111",  # 替换为你的MySQL密码
        "host": "localhost",
        "port": 3306,
        "database": "ecommerce_analysis"
    }
    return create_engine(
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset=utf8mb4"
    )

engine = get_mysql_engine()

# -------------------------- 侧边栏配置 --------------------------
st.sidebar.header("🔍 筛选条件")

# 日期筛选
start_date = st.sidebar.date_input(
    "开始日期",
    value=datetime(2017, 11, 25).date(),
    min_value=datetime(2017, 11, 25).date(),
    max_value=datetime(2017, 12, 3).date()
)
end_date = st.sidebar.date_input(
    "结束日期",
    value=datetime(2017, 12, 3).date(),
    min_value=datetime(2017, 11, 25).date(),
    max_value=datetime(2017, 12, 3).date()
)

# Llama模型配置（纯CPU）
st.sidebar.header("🤖 AI模型设置")
model_path = st.sidebar.text_input(
    "Llama模型路径",
    value=r"F:\ecommerce-user-behavior-analysis\models\llama-2-7b-chat.Q4_K_M.gguf"
)

# 初始化session_state中的llm变量（关键修复）
if 'llm' not in st.session_state:
    st.session_state.llm = None

# 自动检查模型文件并加载（纯CPU）
if st.session_state.llm is None:
    if os.path.exists(model_path):
        with st.sidebar.status("正在自动加载Llama模型..."):
            st.session_state.llm = load_llama_model(model_path)
            if st.session_state.llm:
                st.sidebar.success("模型加载成功！）")
    else:
        st.sidebar.warning("未找到模型文件，请检查路径")
else:
    if st.sidebar.button("重新加载模型"):
        with st.spinner("正在重新加载Llama模型..."):
            st.session_state.llm = load_llama_model(model_path)
        if st.session_state.llm:
            st.sidebar.success("模型重新加载成功！")

# 模型性能监控（仅显示CPU相关，移除GPU）
if 'llm' in st.session_state and st.session_state.llm:
    st.sidebar.subheader("模型状态")
    try:
        st.sidebar.text(f"上下文窗口: {st.session_state.llm.n_ctx} tokens")
        st.sidebar.text(f"CPU线程数: {st.session_state.llm.n_threads}")
        st.sidebar.text("运行模式: 纯CPU（无GPU加速）")
    except AttributeError:
        st.sidebar.text("模型状态：已加载（属性暂不可查）")

# -------------------------- 加载筛选后的数据 --------------------------
@st.cache_data
def load_behavior_data(start, end):
    sql = f"""
        SELECT * FROM user_behavior 
        WHERE date >= '{start}' AND date <= '{end}'
    """
    return pd.read_sql(sql, engine)

df_filtered = load_behavior_data(start_date, end_date)

# -------------------------- 核心指标展示 --------------------------
st.title("📊 电商用户行为分析看板")
st.divider()

# 计算留存率和热销品类
user_retention = calculate_retention(df_filtered)
top_categories = df_filtered[df_filtered["behavior_type"]=="buy"]["category_id"].value_counts().head(3).index.tolist()

# 指标卡片（增加留存率指标）
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    total_users = df_filtered["user_id"].nunique()
    st.metric("总独立用户数", value=f"{total_users:,}")
with col2:
    total_pv = df_filtered[df_filtered["behavior_type"] == "pv"].shape[0]
    st.metric("总浏览量（PV）", value=f"{total_pv:,}")
with col3:
    total_buy = df_filtered[df_filtered["behavior_type"] == "buy"].shape[0]
    st.metric("总购买量", value=f"{total_buy:,}")
with col4:
    conversion = (total_buy / total_pv) * 100 if total_pv > 0 else 0
    st.metric("整体转化率", value=f"{conversion:.2f}%")
with col5:
    st.metric("次日留存率", value=f"{user_retention:.2f}%")

# -------------------------- 转化漏斗图表 --------------------------
st.divider()
st.subheader("转化漏斗分析")
funnel_data = {
    "浏览": df_filtered[df_filtered["behavior_type"] == "pv"]["user_id"].nunique(),
    "收藏": df_filtered[df_filtered["behavior_type"] == "fav"]["user_id"].nunique(),
    "加购": df_filtered[df_filtered["behavior_type"] == "cart"]["user_id"].nunique(),
    "购买": df_filtered[df_filtered["behavior_type"] == "buy"]["user_id"].nunique()
}
funnel_order = ["浏览", "收藏", "加购", "购买"]
funnel_values = [funnel_data[s] for s in funnel_order]

fig_funnel = px.funnel(
    x=funnel_values,
    y=funnel_order,
    color=funnel_order,
    color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
    title="用户行为转化漏斗"
)
st.plotly_chart(fig_funnel, use_container_width=True)

# -------------------------- 用户分群 + 时段分析 + 热销品类 --------------------------
st.divider()
st.subheader("用户分群 & 时段行为 & 热销品类分析")
col1, col2, col3 = st.columns(3)  # 增加一列显示热销品类

# RFM用户分群饼图
with col1:
    rfm_df = pd.read_sql("SELECT user_segment FROM user_rfm", engine)
    segment_counts = rfm_df["user_segment"].value_counts()
    fig_pie = px.pie(
        values=segment_counts.values,
        names=segment_counts.index,
        title="RFM用户分群分布",
        hole=0.3
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# 时段行为分布折线图
with col2:
    hourly_behavior = df_filtered.groupby(["hour", "behavior_name"])["user_id"].count().unstack(fill_value=0)
    fig_hour = px.line(
        hourly_behavior,
        x=hourly_behavior.index,
        y=hourly_behavior.columns,
        title="用户行为时段分布",
        labels={"value": "行为次数", "hour": "小时"},
        markers=True
    )
    st.plotly_chart(fig_hour, use_container_width=True)
    # 提取购买高峰时段
    if "buy" in hourly_behavior.columns and not hourly_behavior["buy"].empty:
        buy_peak = hourly_behavior["buy"].idxmax()
    else:
        buy_peak = "无数据"

# 热销品类TOP5柱状图
with col3:
    if not df_filtered[df_filtered["behavior_type"] == "buy"].empty:
        top5_categories = df_filtered[df_filtered["behavior_type"] == "buy"]["category_id"].value_counts().head(5)
        fig_category = px.bar(
            x=top5_categories.index.astype(str),
            y=top5_categories.values,
            title="热销品类TOP5",
            labels={"x": "品类ID", "y": "购买次数"},
            color=top5_categories.values,
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_category, use_container_width=True)
    else:
        st.info("该时段内无购买数据，无法展示热销品类")

# -------------------------- AI分析建议 --------------------------
st.divider()
st.subheader("🤖 AI生成分析建议")

# 准备分析所需指标
metrics = {
    "start_date": start_date,
    "end_date": end_date,
    "total_users": total_users,
    "total_pv": total_pv,
    "total_buy": total_buy,
    "conversion": conversion,
    "funnel_values": funnel_values,
    "buy_peak": buy_peak,
    "high_value_ratio": (segment_counts.get("高价值用户", 0) / segment_counts.sum() * 100) if segment_counts.sum() > 0 else 0
}

# 生成AI分析（纯CPU）
ai_analysis = "未生成AI分析"
if st.session_state.llm:
    with st.spinner("AI正在分析数据（纯CPU，稍慢）..."):
        ai_analysis = generate_ai_analysis(st.session_state.llm, metrics, df_filtered)
    st.text_area("分析结果", value=ai_analysis, height=200, disabled=True)
else:
    st.warning("请先加载Llama模型以获取AI分析建议（检查模型路径）")

# -------------------------- 报告导出功能 --------------------------
st.divider()
st.subheader("📑 报告导出")

if st.button("生成PDF分析报告"):
    with st.spinner("正在生成PDF报告..."):
        # 准备报告所需数据
        pdf_path = generate_chinese_pdf(
            start_date=start_date,
            end_date=end_date,
            total_users=total_users,
            total_pv=total_pv,
            total_buy=total_buy,
            conversion=conversion,
            funnel_order=funnel_order,
            funnel_values=funnel_values,
            segment_counts=segment_counts,
            buy_peak=buy_peak,
            ai_analysis=ai_analysis,
            top_categories=top_categories,
            user_retention=user_retention
        )
    if pdf_path:
        st.success(f"PDF报告已生成：{pdf_path}")
        # 提供下载功能
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="下载PDF报告",
                data=f,
                file_name="电商用户分析报告.pdf",
                mime="application/pdf"
            )
    else:
        st.error("PDF报告生成失败")

# -------------------------- 数据预览 --------------------------
st.divider()
with st.expander("📁 查看原始数据（前100行）"):
    st.dataframe(df_filtered.head(100), use_container_width=True)