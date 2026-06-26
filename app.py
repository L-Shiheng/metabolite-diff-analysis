import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import matplotlib
import platform
from scipy import stats

# 设置中文字体
def set_chinese_font():
    system = platform.system()
    if system == 'Windows':
        font_list = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'FangSong']
    elif system == 'Darwin':
        font_list = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Apple LiGothic']
    else:
        font_list = ['WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'SimHei', 'DejaVu Sans']
    for font in font_list:
        try:
            matplotlib.rcParams['font.sans-serif'] = [font]
            matplotlib.rcParams['axes.unicode_minus'] = False
            plt.text(0.5, 0.5, '测试', fontsize=10)
            plt.close()
            return True
        except:
            continue
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    return False

st.set_page_config(page_title="代谢物特征消失原因与质量评估", page_icon="🔍", layout="wide")
st.title("🔍 代谢物特征消失原因与数据质量评估")
st.markdown("上传差异报告，分析校正后数据质量是否提升")

uploaded_file = st.file_uploader("📤 上传差异报告 CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    
    # 概览
    total_features = len(df)
    gone_features = len(df[df['diff_type'] == '整个特征消失'])
    kept_features = total_features - gone_features
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总特征数", total_features)
    col2.metric("消失特征", gone_features, delta=f"-{gone_features}")
    col3.metric("保留特征", kept_features)
    col4.metric("有变化特征", len(df[df['diff_type'] != '无差异']) - gone_features if '无差异' in df['diff_type'].values else kept_features)
    
    gone = df[df['diff_type'] == '整个特征消失'].copy()
    kept = df[df['diff_type'] != '整个特征消失'].copy()
    
    # ========== 新增：数据质量评估函数 ==========
    def assess_data_quality(df, gone, kept):
        total_features = len(df)
        gone_count = len(gone)
        kept_count = len(kept)
        gone_ratio = gone_count / total_features if total_features > 0 else 0
        
        gone_single = gone['non_names'].str.contains(';', na=False).apply(lambda x: not x).sum() if gone_count > 0 else 0
        kept_single = kept['non_names'].str.contains(';', na=False).apply(lambda x: not x).sum() if kept_count > 0 else 0
        gone_single_ratio = gone_single / gone_count if gone_count > 0 else 0
        kept_single_ratio = kept_single / kept_count if kept_count > 0 else 0
        
        gone_exmrn = gone['non_names'].str.contains('ExMrn', na=False).sum()
        kept_exmrn = kept['non_names'].str.contains('ExMrn', na=False).sum()
        gone_exmrn_ratio = gone_exmrn / gone_count if gone_count > 0 else 0
        kept_exmrn_ratio = kept_exmrn / kept_count if kept_count > 0 else 0
        
        matched = df[df['diff_type'] != '整个特征消失'].copy()
        if len(matched) > 0:
            non_counts = matched['non_names'].str.split(';').apply(len)
            ds_counts = matched['ds_names'].str.split(';').apply(len)
            avg_non = non_counts.mean()
            avg_ds = ds_counts.mean()
            name_count_change = avg_non - avg_ds
        else:
            avg_non = avg_ds = 0
            name_count_change = 0
        
        def known_ratio(names_str):
            names = [n.strip() for n in str(names_str).split(';') if n.strip()]
            if not names:
                return 0
            known = sum(1 for n in names if 'ExMrn' not in n)
            return known / len(names)
        
        if len(matched) > 0:
            non_known = matched['non_names'].apply(known_ratio).mean()
            ds_known = matched['ds_names'].apply(known_ratio).mean()
            known_change = ds_known - non_known
        else:
            non_known = ds_known = 0
            known_change = 0
        
        reduce_count = len(df[df['diff_type'] == '候选名减少'])
        increase_count = len(df[df['diff_type'] == '候选名增加'])
        change_count = len(df[df['diff_type'] == '候选名改变'])
        
        # 评分
        positive = 0
        if gone_ratio > 0.3:
            positive += 1
        if gone_single_ratio > kept_single_ratio + 0.2:
            positive += 1
        if gone_exmrn_ratio > kept_exmrn_ratio + 0.2:
            positive += 1
        if name_count_change > 0.5:
            positive += 1
        if known_change > 0.05:
            positive += 1
        if reduce_count > increase_count * 1.5:
            positive += 1
        
        if positive >= 4:
            quality = "显著提升"
            color = "green"
            summary = "校正后数据质量明显改善：大量低置信度特征被移除，注释特异性增强。"
        elif positive >= 2:
            quality = "略有提升"
            color = "orange"
            summary = "校正后有一定改善，但效果不突出。"
        else:
            quality = "无明显提升或下降"
            color = "red"
            summary = "校正效果不明显，建议检查参数或原始数据。"
        
        return {
            'gone_ratio': gone_ratio,
            'gone_single_ratio': gone_single_ratio,
            'kept_single_ratio': kept_single_ratio,
            'gone_exmrn_ratio': gone_exmrn_ratio,
            'kept_exmrn_ratio': kept_exmrn_ratio,
            'avg_non': avg_non,
            'avg_ds': avg_ds,
            'name_count_change': name_count_change,
            'non_known': non_known,
            'ds_known': ds_known,
            'known_change': known_change,
            'reduce_count': reduce_count,
            'increase_count': increase_count,
            'change_count': change_count,
            'quality': quality,
            'color': color,
            'summary': summary
        }
    
    quality = assess_data_quality(df, gone, kept)
    
    # 显示质量评估
    st.subheader("📈 数据质量评估：校正是否提升了数据可靠性？")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("校正后质量评级", quality['quality'], delta=None)
        st.success(quality['summary'])
    with col2:
        metrics_df = pd.DataFrame({
            '指标': ['消失特征占比', '消失特征中单候选名比例', '保留特征中单候选名比例',
                     '消失特征中ExMrn比例', '保留特征中ExMrn比例',
                     '候选名平均数量(校正前)', '候选名平均数量(校正后)', '候选名数量变化(减少为正)',
                     '已知代谢物比例(校正前)', '已知代谢物比例(校正后)', '已知代谢物比例变化',
                     '候选名减少特征数', '候选名增加特征数', '候选名改变特征数'],
            '数值': [
                f"{quality['gone_ratio']:.1%}",
                f"{quality['gone_single_ratio']:.1%}",
                f"{quality['kept_single_ratio']:.1%}",
                f"{quality['gone_exmrn_ratio']:.1%}",
                f"{quality['kept_exmrn_ratio']:.1%}",
                f"{quality['avg_non']:.2f}",
                f"{quality['avg_ds']:.2f}",
                f"{quality['name_count_change']:+.2f}",
                f"{quality['non_known']:.1%}",
                f"{quality['ds_known']:.1%}",
                f"{quality['known_change']:+.1%}",
                quality['reduce_count'],
                quality['increase_count'],
                quality['change_count']
            ]
        })
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    
    # 其余统计分析、可视化等（保留之前的代码，略作修改）
    # 此处省略重复代码，实际部署时请将之前版本的可视化、原因推断、下载等部分放在这里
    # 为了简洁，下面给出占位提示
    st.info("此处应包含之前的统计分析和可视化部分，已省略以缩短篇幅。实际使用请合并完整代码。")
    
else:
    st.info("👈 请上传差异报告 CSV 文件")
