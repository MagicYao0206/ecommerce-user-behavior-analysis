import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import warnings
from datetime import datetime
import os
warnings.filterwarnings("ignore")

# -------------------------- 配置MySQL连接 --------------------------
MYSQL_CONFIG = {
    "user": "root",
    "password": "1111",
    "host": "localhost",
    "port": 3306,
    "database": "ecommerce_analysis"
}
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset=utf8mb4"
)

# -------------------------- RFM分析核心 --------------------------
def rfm_analysis():
    # 1. 读取用户汇总数据
    user_summary_df = pd.read_sql("SELECT * FROM user_summary", con=engine)
    print(f"用户总数：{user_summary_df.shape[0]}")

    # 2. 计算RFM指标
    end_date = datetime(2017, 12, 3).date()
    # 转换last_buy_time为datetime，空值转NaT
    user_summary_df["last_buy_time"] = pd.to_datetime(user_summary_df["last_buy_time"], errors="coerce")
    
    # 计算R值（最近购买天数，未购买=999）
    def calc_r_days(row):
        if pd.notna(row["last_buy_time"]):
            return (end_date - row["last_buy_time"].date()).days
        else:
            return 999
    user_summary_df["R"] = user_summary_df.apply(calc_r_days, axis=1)

    # F/M值（购买次数，空值填0）
    user_summary_df["F"] = user_summary_df["buy_count"].fillna(0).astype(int)
    user_summary_df["M"] = user_summary_df["buy_count"].fillna(0).astype(int)

    # 3. 给RFM打分（核心修复：动态适配分箱数）
    # 定义打分函数：不管分多少箱，都映射到1-5分
    def score_rfm(col, ascending=True):
        # 按值排序，计算百分位
        rank = col.rank(method="min", ascending=ascending)
        percent = rank / rank.max()
        # 按百分位映射到1-5分
        score = pd.cut(
            percent,
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],  # 固定5个区间
            labels=[5,4,3,2,1] if ascending else [1,2,3,4,5],
            include_lowest=True
        )
        return score

    # R_score：值越小（越近购买），分数越高（5分最好）
    user_summary_df["R_score"] = score_rfm(user_summary_df["R"], ascending=True)
    # F/M_score：值越大（购买次数越多），分数越高（5分最好）
    user_summary_df["F_score"] = score_rfm(user_summary_df["F"], ascending=False)
    user_summary_df["M_score"] = score_rfm(user_summary_df["M"], ascending=False)

    # 4. 合并分数并分群（处理空值）
    # 空值填充为"0"，避免字符串拼接失败
    user_summary_df["R_score"] = user_summary_df["R_score"].astype(str).fillna("0")
    user_summary_df["F_score"] = user_summary_df["F_score"].astype(str).fillna("0")
    user_summary_df["M_score"] = user_summary_df["M_score"].astype(str).fillna("0")
    user_summary_df["RFM_score"] = user_summary_df["R_score"] + user_summary_df["F_score"] + user_summary_df["M_score"]

    # 分群规则
    def rfm_segment(score):
        # 高价值：R1-2 + F4-5 + M4-5
        if (score[0] in ["1","2"]) and (score[1] in ["4","5"]) and (score[2] in ["4","5"]):
            return "高价值用户"
        # 潜力用户：R1-2 + F1-3 + M1-3
        elif (score[0] in ["1","2"]) and (score[1] in ["1","2","3"]) and (score[2] in ["1","2","3"]):
            return "潜力用户"
        # 流失高价值：R4-5 + F4-5 + M4-5
        elif (score[0] in ["4","5"]) and (score[1] in ["4","5"]) and (score[2] in ["4","5"]):
            return "流失高价值用户"
        # 低价值：R4-5 + F1-2 + M1-2
        elif (score[0] in ["4","5"]) and (score[1] in ["1","2"]) and (score[2] in ["1","2"]):
            return "低价值用户"
        # 未购买用户
        elif score.startswith("0"):
            return "未购买用户"
        # 一般用户
        else:
            return "一般用户"
    user_summary_df["user_segment"] = user_summary_df["RFM_score"].apply(rfm_segment)

    # 5. 可视化分群结果
    plt.rcParams["font.sans-serif"] = ["SimHei"]  # Windows显示中文
    plt.rcParams["axes.unicode_minus"] = False
    plt.figure(figsize=(12, 7))
    
    # 统计分群数量
    segment_counts = user_summary_df["user_segment"].value_counts()
    # 绘制饼图（添加颜色和突出效果）
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57", "#DDA0DD"]
    explode = [0.08 if x == "高价值用户" else 0 for x in segment_counts.index]
    
    plt.pie(
        segment_counts.values,
        labels=segment_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors[:len(segment_counts)],
        explode=explode,
        textprops={"fontsize": 11}
    )
    plt.title("电商用户RFM分群分布", fontsize=16, pad=20)
    plt.ylabel("")
    
    # 保存图片
    save_path = "F:\\ecommerce-user-behavior-analysis\\results\\user_segment_pie.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ 用户分群饼图已保存：{save_path}")

    # 6. 写入MySQL
    user_summary_df.to_sql("user_rfm", engine, if_exists="replace", index=False)
    print("✅ RFM结果已写入MySQL -> user_rfm表")

    # 7. 输出分析结论
    print("\n" + "="*30 + " RFM分析结论 " + "="*30)
    total = user_summary_df.shape[0]
    for seg, cnt in segment_counts.items():
        ratio = (cnt / total) * 100
        print(f"🔸 {seg:10s}：{cnt:>5d}人，占比{ratio:>5.1f}%")

    # 运营建议
    print("\n" + "="*30 + " 运营建议 " + "="*30)
    if segment_counts.get("高价值用户", 0) > 0:
        print("🎯 高价值用户：重点维护，推出会员体系/专属客服")
    if segment_counts.get("流失高价值用户", 0) > total*0.01:
        print("⚠️ 流失高价值用户：推送召回优惠券，短信触达激活")
    if segment_counts.get("未购买用户", 0) > total*0.1:
        print("💡 未购买用户：优化推荐算法，降低首单购买门槛")
    if segment_counts.get("潜力用户", 0) > 0:
        print("🚀 潜力用户：推送满减活动，提升购买频次")

if __name__ == "__main__":
    # 自动创建results文件夹
    result_dir = "F:\\ecommerce-user-behavior-analysis\\results"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
        print(f"📁 已创建文件夹：{result_dir}")
    
    # 运行分析
    rfm_analysis()
    print("\n🎉 RFM分析全部完成！")