import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# -------------------------- MySQL配置 --------------------------
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

# -------------------------- 时段分析 --------------------------
def hourly_analysis():
    # 1. 读取数据
    df = pd.read_sql("SELECT hour, behavior_name, user_id FROM user_behavior", con=engine)

    # 2. 按小时+行为统计次数
    hourly_behavior = df.groupby(["hour", "behavior_name"])["user_id"].count().unstack(fill_value=0)

    # 3. 可视化
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.figure(figsize=(12, 6))
    hourly_behavior.plot(kind="line", marker="o", linewidth=2)
    plt.title("电商用户行为时段分布（小时维度）")
    plt.xlabel("小时")
    plt.ylabel("行为次数")
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.legend(title="行为类型")
    plt.tight_layout()
    # 保存图片
    plt.savefig("F:\\ecommerce-user-behavior-analysis\\results\\hourly_behavior.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("✅ 时段分析图已保存！")

    # 4. 输出结论
    pv_peak = hourly_behavior["浏览"].idxmax()
    buy_peak = hourly_behavior["购买"].idxmax()
    print("\n=== 时段分析结论 ===")
    print(f"浏览高峰：{pv_peak}点，购买高峰：{buy_peak}点")
    print(f"建议：{buy_peak-1}点推送优惠券，提升转化！")

if __name__ == "__main__":
    hourly_analysis()