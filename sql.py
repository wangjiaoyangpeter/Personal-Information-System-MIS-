import sqlite3
from streamlit import *
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

# 页面配置
set_page_config(
    page_title="个人信息管理系统",
    page_icon="📋",
    layout="wide"
)

# 自定义CSS样式
css = '''
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        width: 100%;
        font-weight: bold;
    }
    .feature-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 1.5rem;
    }
    .stat-box {
        background-color: #e6f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        flex: 1;
        margin: 0 0.5rem;
    }
    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
        color: #0066cc;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
</style>
'''
markdown(css, unsafe_allow_html=True)

# 数据库连接
conn = sqlite3.connect('C:/Users/21125/PycharmProjects/PythonProject4/test.db')
conn.execute('PRAGMA foreign_keys = ON')
tname="Title"
conn.execute(f'''
CREATE TABLE IF NOT EXISTS {tname}
(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
name TEXT,title TEXT,category TEXT,created_at TEXT,notes TEXT) ;
''')
conn.commit()
CATEGORY = ['荣誉', '教育经历', '竞赛', '证书', '账号', '其他']
info=['id','title','category','notes','created_at']

def insert_data():
    with container():
        markdown("### 📝 添加新记录")
        with form ('add_form',clear_on_submit=1):
            new= {}
            new ['name']= text_input('姓名', placeholder='请输入姓名')
            new['title'] = text_input('标题*', placeholder='例如：三好学生')
            new['category'] = selectbox('类别', CATEGORY, index=0)
            new['notes'] = text_area("备注（可选）", placeholder="关键信息、链接或行动项…", height=100)
            submitted = form_submit_button('保存', type="primary", use_container_width=1)

        if submitted:
            if new['title'] == '':
                warning('标题不能为空！')
            else:
                # 使用参数化查询防止SQL注入
                conn.execute(
                    f'INSERT INTO {tname}(name, title, category, created_at, notes) VALUES(?, ?, ?, datetime("now"), ?)',
                    (new['name'], new['title'], new['category'], new['notes'])
                )
                conn.commit()
                success('保存成功！')

def select_data():
    df = pd.read_sql(f'select * from {tname}', conn)
    
    with container():
        markdown("### 🔍 查询数据")
        
        # 添加搜索框
        search_term = text_input("搜索关键词", placeholder="在所有字段中搜索...")
        
        # 高级筛选选项
        with form('select_form'):
            col1, col2 = columns([1, 1])
            
            with col1:
                case = multiselect("选择筛选字段", info, default=[])
                
            with col2:
                if len(df) > 0:
                    date_filter = selectbox(
                        "按时间筛选", 
                        ["全部", "今天", "本周", "本月", "自定义"], 
                        index=0
                    )
            
            # 生成每个选中字段的筛选选项
            cases = []
            for i in case:
                cases_i = multiselect(f"选择 {i}", df[i].unique())
                if len(cases_i) > 0:
                    if len(cases_i) == 1:
                        cases.append(f"{i} = \"{cases_i[0]}\"")
                    else:
                        cases.append(f"{i} IN {tuple(cases_i)}")
            
            select_button = form_submit_button('应用筛选', type="primary", use_container_width=1)
        
        # 构建查询条件
        query_conditions = []
        
        # 搜索关键词条件
        if search_term:
            search_conditions = [f"{col} LIKE '%{search_term}%'" for col in ['name', 'title', 'notes']]
            query_conditions.append(f"({' OR '.join(search_conditions)})")
        
        # 添加字段筛选条件
        query_conditions.extend(cases)
        
        # 添加时间筛选条件
        if date_filter == "今天":
            query_conditions.append("date(created_at) = date('now')")
        elif date_filter == "本周":
            query_conditions.append("strftime('%W', created_at) = strftime('%W', 'now')")
        elif date_filter == "本月":
            query_conditions.append("strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')")
        
        # 构建最终查询
        if query_conditions:
            cases_sum = " AND ".join(query_conditions)
            dfs = pd.read_sql(f"SELECT * FROM {tname} WHERE {cases_sum}", conn)
        else:
            dfs = df.copy()
        
        # 显示结果
        if len(dfs) > 0:
            success(f"找到 {len(dfs)} 条记录")
            
            # 添加排序选项
            sort_by = selectbox("排序字段", info, index=0)
            ascending = checkbox("升序排列", value=True)
            dfs_sorted = dfs.sort_values(by=sort_by, ascending=ascending)
            
            # 显示表格
            data_editor(dfs_sorted, use_container_width=True, hide_index=True)
            
            # 导出功能
            if len(dfs_sorted) > 0:
                csv = dfs_sorted.to_csv(index=False).encode('utf-8')
                download_button(
                    label="📥 导出数据为CSV",
                    data=csv,
                    file_name=f"personal_info_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
        else:
            info("没有找到符合条件的记录")

def delete_data():
    df = pd.read_sql(f'select * from {tname}', conn)
    
    with container():
        markdown("### 🗑️ 删除记录")
        
        if len(df) == 0:
            info("没有可删除的记录")
            return
        
        # 批量删除功能
        delete_mode = selectbox("删除模式", ["单个删除", "批量删除"], index=0)
        
        with form('delete_form'):
            if delete_mode == "单个删除":
                ids = selectbox("选择要删除的记录ID", df['id'].unique())
                delete_button = form_submit_button('删除记录', type="primary", use_container_width=1)
                
                if delete_button:
                    conn.execute(f'DELETE FROM {tname} WHERE id = ?', (ids,))
                    conn.commit()
                    success(f'ID为 {ids} 的记录已成功删除！')
            else:
                # 批量删除
                selected_ids = multiselect("选择要删除的记录ID", df['id'].unique())
                delete_button = form_submit_button('批量删除', type="primary", use_container_width=1)
                
                if delete_button and selected_ids:
                    # 使用参数化查询
                    placeholders = ','.join('?' for _ in selected_ids)
                    conn.execute(f'DELETE FROM {tname} WHERE id IN ({placeholders})', selected_ids)
                    conn.commit()
                    success(f'已成功删除 {len(selected_ids)} 条记录！')
                elif delete_button and not selected_ids:
                    warning('请至少选择一条记录进行删除')

def update_data():
    df = pd.read_sql(f'select * from {tname}', conn)
    
    with container():
        markdown("### ✏️ 更新记录")
        
        if len(df) == 0:
            info("没有可更新的记录")
            return
        
        # 选择要更新的记录
        row = selectbox("选择要更新的记录", df['id'].unique(), index=0)
        
        # 显示当前记录信息
        current_record = df[df['id'] == row].iloc[0]
        with expander("查看当前记录详情", expanded=True):
            for col_name, value in current_record.items():
                markdown(f"**{col_name}**: {value}")
        
        # 选择要更新的字段
        col = selectbox("选择要更新的字段", info, index=0)
        
        with form('update_form'):
            # 根据字段类型显示不同的输入控件
            if col == 'notes':
                # 显示当前备注内容作为默认值
                current_value = current_record['notes'] if pd.notna(current_record['notes']) else ''
                new = text_area("新备注内容", value=current_value, height=100)
            elif col == 'category':
                # 显示当前类别作为默认选中项
                current_value = current_record['category'] if pd.notna(current_record['category']) else CATEGORY[0]
                category_index = CATEGORY.index(current_value) if current_value in CATEGORY else 0
                new = selectbox('新类别', CATEGORY, index=category_index)
            else:
                # 对于其他字段，显示当前值作为默认值
                current_value = current_record[col] if pd.notna(current_record[col]) else ''
                new = text_input(f"新的{col}", value=str(current_value))
            
            update_button_2 = form_submit_button('更新记录', type="primary", use_container_width=1)
        
        if update_button_2:
            # 使用参数化查询防止SQL注入
            conn.execute(
                f'UPDATE {tname} SET {col} = ? WHERE id = ?',
                (new, row)
            )
            conn.commit()
            success(f'ID为 {row} 的记录已成功更新！')

# 显示页面标题
with container():
    markdown("# 个人信息管理系统")
    markdown("一个用于管理个人荣誉、教育经历、竞赛、证书等信息的综合平台")

audio("audio.mp3",autoplay=True)
# 创建居中的列布局来显示图片
col1, col2, col3 = columns([1, 3, 1])
with col2:
    image("cover.jpg", use_column_width=True)  # 使用列宽度自适应显示

# 数据统计区域
df = pd.read_sql(f'select * from {tname}', conn)
if len(df) > 0 and checkbox("显示数据统计", value=True):
    with container():
        markdown("## 📊 数据统计概览")
        
        # 计算统计数据
        total_records = len(df)
        category_counts = df['category'].value_counts()
        
        # 显示基本统计信息
        col1, col2, col3 = columns(3)
        with col1:
            metric("总记录数", total_records)
        with col2:
            metric("类别数量", len(category_counts))
        with col3:
            metric("最近更新", df['created_at'].max())
        
        # 显示类别分布图表
        with container():
            markdown("### 各类别记录分布")
            fig, ax = plt.subplots(figsize=(10, 6))
            category_counts.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_xlabel('类别')
            ax.set_ylabel('记录数')
            ax.set_title('各类别记录数量分布')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            plotly_chart(fig)

# 功能选择菜单
with container():
    markdown("## 🛠️ 功能菜单")
    mode = selectbox(
        "选择操作模式", 
        ['查看所有数据', '添加记录', '更新记录', '删除记录', '查询数据', '导入数据'], 
        index=0,
        format_func=lambda x: {
            '查看所有数据': '📋 查看所有数据',
            '添加记录': '➕ 添加记录',
            '更新记录': '✏️ 更新记录',
            '删除记录': '🗑️ 删除记录',
            '查询数据': '🔍 查询数据',
            '导入数据': '📥 导入数据'
        }.get(x, x)
    )

# 根据选择的模式执行相应功能
if mode == '添加记录':
    insert_data()
elif mode == '更新记录':
    update_data()
elif mode == '删除记录':
    delete_data()
elif mode == '查询数据':
    select_data()
elif mode == '导入数据':
    with container():
        markdown("### 📥 导入数据")
        uploaded_file = file_uploader("选择CSV文件进行导入", type="csv")
        
        if uploaded_file is not None:
            try:
                # 读取上传的CSV文件
                df_import = pd.read_csv(uploaded_file)
                
                # 显示导入的数据预览
                markdown("#### 导入数据预览")
                write(df_import.head())
                
                # 确认导入
                if button("确认导入数据", type="primary", use_container_width=True):
                    # 导入数据到数据库
                    for _, row in df_import.iterrows():
                        # 检查必要的字段是否存在
                        if 'title' in row and pd.notna(row['title']):
                            # 构建插入数据
                            name = row['name'] if 'name' in row and pd.notna(row['name']) else ''
                            title = row['title']
                            category = row['category'] if 'category' in row and pd.notna(row['category']) else '其他'
                            notes = row['notes'] if 'notes' in row and pd.notna(row['notes']) else ''
                            
                            # 插入数据
                            conn.execute(
                                f'INSERT INTO {tname}(name, title, category, created_at, notes) VALUES(?, ?, ?, datetime("now"), ?)',
                                (name, title, category, notes)
                            )
                    
                    conn.commit()
                    success(f"成功导入 {len(df_import)} 条记录！")
            except Exception as e:
                error(f"导入失败: {str(e)}")
else:  # 查看所有数据
    with container():
        markdown("### 📋 所有记录")
        
        if len(df) > 0:
            # 显示所有数据
            data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                disabled=True  # 只读模式
            )
            
            # 导出所有数据
            csv = df.to_csv(index=False).encode('utf-8')
            download_button(
                label="📥 导出所有数据为CSV",
                data=csv,
                file_name=f"all_personal_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                use_container_width=True
            )

            # 复制到剪贴板
            if button("复制所有数据到剪贴板", use_container_width=True):
                df.to_clipboard(index=False)
                success("所有数据已复制到剪贴板")

        else:
            info("暂无记录，请添加新记录")

# 页脚
with container():
    markdown("---")
    markdown("© 2024 个人信息管理系统 | 保持您的重要信息有序管理")

# 关闭数据库连接
conn.close()