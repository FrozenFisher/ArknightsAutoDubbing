#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看parquet文件的数据类型
"""

import pandas as pd
import os

# 读取parquet文件
parquet_path = os.path.join('lib', 'ref', 'table.parquet')
df = pd.read_parquet(parquet_path)

print("=== 数据类型信息 ===")
print(df.dtypes)

print("\n=== 每列的非空值数量 ===")
print(df.count())

print("\n=== 查看unlock_param列的内容 ===")
print("unlock_param列的唯一值:")
print(df['unlock_param'].value_counts().head(10))

print("\n=== 查看unlock_param列的数据类型 ===")
print(f"unlock_param列类型: {df['unlock_param'].dtype}")
print(f"unlock_param列是否包含列表: {df['unlock_param'].apply(lambda x: isinstance(x, list)).any()}")

# 查看一些示例数据
print("\n=== 查看前5行数据 ===")
for col in ['unlock_param', 'lock_description', 'place_type']:
    print(f"\n{col}列的前5个值:")
    print(df[col].head()) 