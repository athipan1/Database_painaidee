#!/usr/bin/env python3
"""
Hugging Face Spaces compatible app.py
A simplified Gradio interface for Database Painaidee API
"""

import gradio as gr
import requests
import json
import os
import sqlite3
from typing import Dict, List, Any

# Simple in-memory database for demo purposes (since HF Spaces has limitations)
class SimpleDB:
    def __init__(self):
        self.attractions = [
            {
                "id": 1,
                "name": "วัดพระแก้ว",
                "name_en": "Temple of the Emerald Buddha",
                "province": "กรุงเทพมหานคร",
                "province_en": "Bangkok",
                "description": "วัดที่มีความสำคัญทางประวัติศาสตร์และศาสนา",
                "category": "วัด",
                "latitude": 13.7527,
                "longitude": 100.4925
            },
            {
                "id": 2,
                "name": "พระบรมมหาราชวัง",
                "name_en": "Grand Palace",
                "province": "กรุงเทพมหานคร", 
                "province_en": "Bangkok",
                "description": "พระราชวังที่เป็นสถานที่ท่องเที่ยวสำคัญ",
                "category": "พระราชวัง",
                "latitude": 13.7500,
                "longitude": 100.4927
            },
            {
                "id": 3,
                "name": "เกาะพีพี",
                "name_en": "Phi Phi Islands",
                "province": "กระบี่",
                "province_en": "Krabi", 
                "description": "เกาะที่มีความสวยงามทางธรรมชาติ",
                "category": "เกาะ",
                "latitude": 7.7407,
                "longitude": 98.7784
            }
        ]
    
    def search_attractions(self, query: str = "", province: str = "", category: str = "") -> List[Dict]:
        results = self.attractions.copy()
        
        if query:
            results = [a for a in results if query.lower() in a['name'].lower() or 
                      query.lower() in a['name_en'].lower() or
                      query.lower() in a['description'].lower()]
        
        if province:
            results = [a for a in results if province.lower() in a['province'].lower() or 
                      province.lower() in a['province_en'].lower()]
        
        if category:
            results = [a for a in results if category.lower() in a['category'].lower()]
        
        return results

# Initialize database
db = SimpleDB()

def search_attractions(query: str, province: str, category: str) -> str:
    """Search for attractions based on criteria"""
    try:
        results = db.search_attractions(query, province, category)
        
        if not results:
            return "ไม่พบสถานที่ท่องเที่ยวที่ตรงกับเงื่อนไข / No attractions found matching the criteria"
        
        output = f"**พบสถานที่ท่องเที่ยว {len(results)} แห่ง / Found {len(results)} attractions:**\n\n"
        
        for attraction in results:
            output += f"🏛️ **{attraction['name']}** ({attraction['name_en']})\n"
            output += f"📍 จังหวัด: {attraction['province']} / Province: {attraction['province_en']}\n"
            output += f"🏷️ ประเภท: {attraction['category']} / Category: {attraction['category']}\n"
            output += f"📝 {attraction['description']}\n"
            output += f"🌍 พิกัด: {attraction['latitude']}, {attraction['longitude']}\n"
            output += "---\n"
        
        return output
        
    except Exception as e:
        return f"เกิดข้อผิดพลาด / Error: {str(e)}"

def get_api_info() -> str:
    """Get API information"""
    info = """
# 🚀 Database Painaidee API - ระบบจัดการข้อมูลสถานที่ท่องเที่ยว

**ไปไหนดี** - ระบบจัดการข้อมูลสถานที่ท่องเที่ยวด้วย AI และ Big Data

## ✨ คุณสมบัติหลัก / Main Features:
- 🏛️ **ข้อมูลสถานที่ท่องเที่ยวไทย** / Thai attractions database
- 🤖 **AI-Powered Intelligence** - การแนะนำและวิเคราะห์พื้นที่
- 📊 **Behavior Analytics** - การติดตามและวิเคราะห์พฤติกรรมผู้ใช้
- 🗺️ **Auto-Geocoding** - ระบบแปลงที่อยู่เป็นพิกัดอัตโนมัติ
- ⚡ **Real-time Dashboard** - แดชบอร์ดแสดงข้อมูลแบบเรียลไทม์

## 🔗 API Endpoints:
- `GET /api/attractions` - ดึงข้อมูลสถานที่ท่องเที่ยวทั้งหมด
- `POST /api/attractions/sync` - ซิงค์ข้อมูลจาก API ภายนอก
- `GET /api/dashboard/` - หน้าแดชบอร์ด
- `POST /api/ai/keywords/extract` - แยกคำสำคัญด้วย AI
- `POST /api/behavior/track` - ติดตามพฤติกรรมผู้ใช้

## 🛠️ เทคโนโลยีที่ใช้ / Technology Stack:
- **Backend**: Flask + PostgreSQL + Redis
- **Background Tasks**: Celery
- **AI/ML**: Transformers, Scikit-learn
- **Containerization**: Docker + Docker Compose
- **Load Balancing**: Nginx

---
*นี่คือ Demo เวอร์ชัน สำหรับการใช้งานจริงโปรดดู Repository หลัก*
*This is a demo version. For full functionality, please refer to the main repository.*
    """
    return info

def get_sample_queries() -> str:
    """Get sample search queries"""
    return """
## 🔍 ตัวอย่างการค้นหา / Sample Queries:

**ค้นหาตามชื่อ / Search by name:**
- วัดพระแก้ว
- Grand Palace
- เกาะพีพี

**ค้นหาตามจังหวัด / Search by province:**
- กรุงเทพมหานคร
- Bangkok  
- กระบี่
- Krabi

**ค้นหาตามประเภท / Search by category:**
- วัด (Temple)
- พระราชวัง (Palace)
- เกาะ (Island)

**การค้นหาแบบผสม / Combined search:**
- ใส่คำค้นหาหลายคำพร้อมกัน
- Enter multiple search terms together
    """

# Create Gradio interface
with gr.Blocks(title="Database Painaidee API Demo", theme=gr.themes.Soft()) as app:
    gr.HTML("""
    <div style="text-align: center; padding: 20px;">
        <h1>🏛️ Database Painaidee API Demo</h1>
        <h2>ระบบจัดการข้อมูลสถานที่ท่องเที่ยวไทย</h2>
        <p><strong>Thai Attractions Database Management System</strong></p>
    </div>
    """)
    
    with gr.Tabs():
        with gr.Tab("🔍 ค้นหาสถานที่ท่องเที่ยว / Search Attractions"):
            with gr.Row():
                with gr.Column():
                    query_input = gr.Textbox(
                        label="คำค้นหา / Search Query",
                        placeholder="ชื่อสถานที่ท่องเที่ยว / Attraction name",
                        value=""
                    )
                    province_input = gr.Textbox(
                        label="จังหวัด / Province", 
                        placeholder="กรุงเทพมหานคร, Bangkok",
                        value=""
                    )
                    category_input = gr.Textbox(
                        label="ประเภท / Category",
                        placeholder="วัด, เกาะ, พระราชวัง",
                        value=""
                    )
                    search_btn = gr.Button("🔍 ค้นหา / Search", variant="primary")
                
                with gr.Column():
                    results_output = gr.Markdown(
                        label="ผลการค้นหา / Search Results",
                        value="พร้อมค้นหาสถานที่ท่องเที่ยว / Ready to search attractions"
                    )
            
            search_btn.click(
                fn=search_attractions,
                inputs=[query_input, province_input, category_input],
                outputs=results_output
            )
        
        with gr.Tab("ℹ️ ข้อมูล API / API Info"):
            api_info_output = gr.Markdown(value=get_api_info())
        
        with gr.Tab("💡 ตัวอย่างการใช้งาน / Usage Examples"):
            examples_output = gr.Markdown(value=get_sample_queries())
    
    gr.HTML("""
    <div style="text-align: center; padding: 20px; margin-top: 20px; border-top: 1px solid #eee;">
        <p><strong>🚀 สำหรับการใช้งานเต็มรูปแบบ / For full functionality:</strong></p>
        <p>
            <a href="https://github.com/athipan1/Database_painaidee" target="_blank" 
               style="margin: 0 10px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                📂 GitHub Repository
            </a>
            <a href="https://colab.research.google.com/github/athipan1/Database_painaidee/blob/main/Database_Painaidee_Colab.ipynb" target="_blank"
               style="margin: 0 10px; padding: 8px 16px; background: #f57c00; color: white; text-decoration: none; border-radius: 4px;">
                📓 Run on Colab
            </a>
        </p>
    </div>
    """)

if __name__ == "__main__":
    app.launch()