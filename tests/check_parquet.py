#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看parquet文件结构
"""

import pandas as pd
import os

# 读取parquet文件
parquet_path = os.path.join('lib', 'ref', 'table.parquet')
df = pd.read_parquet(parquet_path)

print("=== Parquet文件结构 ===")
print(f"行数: {len(df)}")
print(f"列数: {len(df.columns)}")
print(f"列名: {list(df.columns)}")
print("\n=== 前5行数据 ===")
print(df.head())
print("\n=== 数据类型 ===")
print(df.dtypes) 