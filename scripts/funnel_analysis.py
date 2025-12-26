import pandas as pd
import plotly.express as px
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

# -------------------------- 漏斗分析 --------------------------
def funnel_analysis():
    # 1. 读取数据
    df = pd.read_sql("SELECT * FROM user_behavior", con=engine)

    # 2. 计算各环节独立用户数
    funnel_data = {
        "浏览": df[df["behavior_type"]=="pv"]["user_id"].nunique(),
        "收藏": df[df["behavior_type"]=="fav"]["user_id"].nunique(),
        "加购": df[df["behavior_type"]=="cart"]["user_id"].nunique(),
        "购买": df[df["behavior_type"]=="buy"]["user_id"].nunique()
    }
    funnel_order = ["浏览", "收藏", "加购", "购买"]
    funnel_values = [funnel_data[step] for step in funnel_order]

    # 3. 计算转化率
    conversion_rates = []
    for i in range(1, len(funnel_values)):
        rate = (funnel_values[i] / funnel_values[i-1]) * 100
        conversion_rates.append(f"{rate:.2f}%")

    # 4. 绘制漏斗图（保存为HTML）
    fig = px.funnel(
        x=funnel_values,
        y=funnel_order,
        title="电商用户转化漏斗",
        labels={"x": "独立用户数", "y": "转化环节"}
    )
    # 添加转化率标注
    for i, rate in enumerate(conversion_rates):
        fig.add_annotation(
            x=(funnel_values[i] + funnel_values[i+1])/2,
            y=i+0.5,
            text=f"转化率：{rate}",
            showarrow=False
        )
    # 保存HTML文件
    fig.write_html("F:\\ecommerce-user-behavior-analysis\\results\\funnel_analysis.html")
    print("✅ 漏斗图已保存！")

    # 5. 输出结论
    print("\n=== 转化漏斗结论 ===")
    print(f"浏览→收藏：{conversion_rates[0]}")
    print(f"收藏→加购：{conversion_rates[1]}")
    print(f"加购→购买：{conversion_rates[2]}")
    if float(conversion_rates[-1].replace("%", "")) < 5:
        print("⚠️ 加购→购买转化率低于5%，建议优化下单流程！")

if __name__ == "__main__":
    funnel_analysis()