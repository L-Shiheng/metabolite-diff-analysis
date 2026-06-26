import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO

st.set_page_config(
    page_title="代谢物差异消失原因分析",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 代谢物特征消失原因分析")
st.markdown("上传 `metabolite_diff` 报告，自动分析哪些特征在校正后消失，并推测可能原因")

# 文件上传
uploaded_file = st.file_uploader(
    "📤 上传差异报告 CSV 文件",
    type=["csv"],
    help="请上传由代谢物注释差异对比工具生成的 CSV 报告"
)

if uploaded_file is not None:
    # 读取数据
    df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    
    # 显示数据概览
    st.subheader("📊 数据概览")
    col1, col2, col3, col4 = st.columns(4)
    
    total_features = len(df)
    gone_features = len(df[df['diff_type'] == '整个特征消失'])
    kept_features = len(df[df['diff_type'] != '整个特征消失'])
    changed_features = kept_features - len(df[df['diff_type'] == '无差异']) if '无差异' in df['diff_type'].values else kept_features
    
    col1.metric("总特征数", total_features)
    col2.metric("消失特征", gone_features, delta=f"-{gone_features}")
    col3.metric("保留特征", kept_features)
    col4.metric("有变化特征", changed_features)
    
    # 分离数据
    gone = df[df['diff_type'] == '整个特征消失'].copy()
    kept = df[df['diff_type'] != '整个特征消失'].copy()
    
    # 统计分析
    st.subheader("📈 统计分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**m/z 分布对比**")
        mz_stats = pd.DataFrame({
            '统计量': ['最小值', '最大值', '平均值', '中位数'],
            '消失特征': [
                f"{gone['mz_non'].min():.4f}",
                f"{gone['mz_non'].max():.4f}",
                f"{gone['mz_non'].mean():.2f}",
                f"{gone['mz_non'].median():.2f}"
            ],
            '保留特征': [
                f"{kept['mz_non'].min():.4f}",
                f"{kept['mz_non'].max():.4f}",
                f"{kept['mz_non'].mean():.2f}",
                f"{kept['mz_non'].median():.2f}"
            ]
        })
        st.table(mz_stats)
        
    with col2:
        st.markdown("**保留时间分布对比**")
        rt_stats = pd.DataFrame({
            '统计量': ['最小值', '最大值', '平均值', '中位数'],
            '消失特征': [
                f"{gone['rt_non'].min():.2f}",
                f"{gone['rt_non'].max():.2f}",
                f"{gone['rt_non'].mean():.2f}",
                f"{gone['rt_non'].median():.2f}"
            ],
            '保留特征': [
                f"{kept['rt_non'].min():.2f}",
                f"{kept['rt_non'].max():.2f}",
                f"{kept['rt_non'].mean():.2f}",
                f"{kept['rt_non'].median():.2f}"
            ]
        })
        st.table(rt_stats)
    
    # 化合物特征分析
    st.subheader("🧬 化合物特征分析")
    
    # 检查是否包含 ExMrn
    gone_has_exmrn = gone['non_names'].str.contains('ExMrn', na=False).sum()
    kept_has_exmrn = kept['non_names'].str.contains('ExMrn', na=False).sum()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**含 ExMrn 编号的比例**")
        exmrn_data = pd.DataFrame({
            '类型': ['消失特征', '保留特征'],
            '含 ExMrn 数量': [gone_has_exmrn, kept_has_exmrn],
            '总数': [len(gone), len(kept)],
            '比例': [
                f"{gone_has_exmrn/len(gone)*100:.1f}%",
                f"{kept_has_exmrn/len(kept)*100:.1f}%"
            ]
        })
        st.table(exmrn_data)
    
    with col2:
        st.markdown("**候选名数量对比**")
        gone_name_count = gone['non_names'].str.split(';').apply(len)
        kept_name_count = kept['non_names'].str.split(';').apply(len)
        
        name_count_data = pd.DataFrame({
            '统计量': ['平均值', '中位数', '最小值', '最大值'],
            '消失特征': [
                f"{gone_name_count.mean():.1f}",
                f"{gone_name_count.median():.0f}",
                f"{gone_name_count.min():.0f}",
                f"{gone_name_count.max():.0f}"
            ],
            '保留特征': [
                f"{kept_name_count.mean():.1f}",
                f"{kept_name_count.median():.0f}",
                f"{kept_name_count.min():.0f}",
                f"{kept_name_count.max():.0f}"
            ]
        })
        st.table(name_count_data)
    
    # 可视化
    st.subheader("📊 可视化分析")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. mz-rt 散点图
    ax1 = axes[0, 0]
    ax1.scatter(kept['rt_non'], kept['mz_non'], label='保留特征', alpha=0.6, color='green', s=50)
    ax1.scatter(gone['rt_non'], gone['mz_non'], label='消失特征', alpha=0.8, color='red', s=50, marker='x')
    ax1.set_xlabel('保留时间 (min)')
    ax1.set_ylabel('m/z')
    ax1.set_title('特征分布：保留 vs 消失')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # 2. mz 分布直方图
    ax2 = axes[0, 1]
    ax2.hist(gone['mz_non'], bins=10, alpha=0.5, label='消失特征', color='red')
    ax2.hist(kept['mz_non'], bins=10, alpha=0.5, label='保留特征', color='green')
    ax2.set_xlabel('m/z')
    ax2.set_ylabel('频数')
    ax2.set_title('m/z 分布对比')
    ax2.legend()
    
    # 3. rt 分布直方图
    ax3 = axes[1, 0]
    ax3.hist(gone['rt_non'], bins=10, alpha=0.5, label='消失特征', color='red')
    ax3.hist(kept['rt_non'], bins=10, alpha=0.5, label='保留特征', color='green')
    ax3.set_xlabel('保留时间 (min)')
    ax3.set_ylabel('频数')
    ax3.set_title('保留时间分布对比')
    ax3.legend()
    
    # 4. 候选名数量箱线图
    ax4 = axes[1, 1]
    bp = ax4.boxplot([gone_name_count, kept_name_count], 
                     labels=['消失特征', '保留特征'],
                     patch_artist=True)
    bp['boxes'][0].set_facecolor('red')
    bp['boxes'][1].set_facecolor('green')
    ax4.set_ylabel('候选名数量')
    ax4.set_title('候选名数量对比')
    ax4.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # 原因推断
    st.subheader("🔎 消失原因推断")
    
    reasons = []
    
    # 判断 mz 分布差异
    mz_diff = abs(gone['mz_non'].mean() - kept['mz_non'].mean())
    if mz_diff > 50:
        reasons.append("⚠️ 消失特征的 m/z 分布与保留特征显著不同，可能存在质谱范围过滤")
    
    # 判断 rt 分布差异
    rt_diff = abs(gone['rt_non'].mean() - kept['rt_non'].mean())
    if rt_diff > 30:
        reasons.append("⚠️ 消失特征的保留时间分布与保留特征显著不同，可能存在保留时间窗口过滤")
    
    # 判断 ExMrn 比例
    gone_exmrn_ratio = gone_has_exmrn / len(gone) if len(gone) > 0 else 0
    kept_exmrn_ratio = kept_has_exmrn / len(kept) if len(kept) > 0 else 0
    if gone_exmrn_ratio > kept_exmrn_ratio + 0.3:
        reasons.append("⚠️ 消失特征中未知编号 (ExMrn) 比例显著更高，可能是低置信度注释被过滤")
    
    # 判断候选名数量
    gone_avg_names = gone_name_count.mean()
    kept_avg_names = kept_name_count.mean()
    if gone_avg_names < kept_avg_names - 1:
        reasons.append("⚠️ 消失特征的候选名数量明显更少，可能是单候选名或低匹配质量特征被过滤")
    
    # 如果以上都没有
    if not reasons:
        reasons.append("✅ 未发现明显的系统性偏差，消失可能是随机的（如低丰度噪音峰）或由校正算法的特定阈值引起")
        reasons.append("💡 建议检查校正参数设置，或对比原始数据的峰强度信息")
    
    for reason in reasons:
        st.write(reason)
    
    # 显示消失特征详情
    with st.expander("📋 查看所有消失特征详情"):
        st.dataframe(
            gone[['mz_non', 'rt_non', 'non_names']].reset_index(drop=True),
            use_container_width=True
        )
    
    # 下载分析报告
    st.subheader("📥 导出分析结果")
    
    # 生成文本报告
    report = f"""
代谢物特征消失原因分析报告
{'='*50}

分析时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

数据概览:
- 总特征数: {total_features}
- 消失特征数: {gone_features} ({gone_features/total_features*100:.1f}%)
- 保留特征数: {kept_features} ({kept_features/total_features*100:.1f}%)

m/z 分布:
- 消失特征: 平均值 {gone['mz_non'].mean():.2f}, 范围 {gone['mz_non'].min():.4f} - {gone['mz_non'].max():.4f}
- 保留特征: 平均值 {kept['mz_non'].mean():.2f}, 范围 {kept['mz_non'].min():.4f} - {kept['mz_non'].max():.4f}

保留时间分布:
- 消失特征: 平均值 {gone['rt_non'].mean():.2f}, 范围 {gone['rt_non'].min():.2f} - {gone['rt_non'].max():.2f}
- 保留特征: 平均值 {kept['rt_non'].mean():.2f}, 范围 {kept['rt_non'].min():.2f} - {kept['rt_non'].max():.2f}

含 ExMrn 编号比例:
- 消失特征: {gone_has_exmrn}/{len(gone)} ({gone_has_exmrn/len(gone)*100:.1f}%)
- 保留特征: {kept_has_exmrn}/{len(kept)} ({kept_has_exmrn/len(kept)*100:.1f}%)

候选名数量 (平均值):
- 消失特征: {gone_name_count.mean():.1f}
- 保留特征: {kept_name_count.mean():.1f}

原因推断:
{chr(10).join(reasons)}

消失特征列表:
{gone[['mz_non', 'rt_non', 'non_names']].to_string(index=False)}
"""
    
    st.download_button(
        label="📄 下载分析报告 (TXT)",
        data=report.encode('utf-8'),
        file_name=f"消失原因分析报告_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
    
    # 下载图表
    from io import BytesIO
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    st.download_button(
        label="📊 下载可视化图表 (PNG)",
        data=buf.getvalue(),
        file_name=f"特征分析图_{pd.Timestamp.now().strftime('%Y%m%d')}.png",
        mime="image/png"
    )

else:
    st.info("👈 请上传差异报告 CSV 文件开始分析")
    
    # 显示示例数据格式
    with st.expander("📖 查看所需 CSV 格式"):
        st.markdown("""
        您的 CSV 文件应包含以下列：
        - `mz_non`: 校正前的 m/z
        - `rt_non`: 校正前的保留时间
        - `mz_ds`: 校正后的 m/z (为空表示特征消失)
        - `rt_ds`: 校正后的保留时间 (为空表示特征消失)
        - `non_names`: 校正前的候选代谢物名称 (分号分隔)
        - `ds_names`: 校正后的候选代谢物名称 (分号分隔)
        - `missing_names`: 缺失的名称
        - `diff_type`: 差异类型 (包含 "整个特征消失")
        - `reason`: 原因说明
        
        示例数据：
