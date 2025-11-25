import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import sys
#コード全体の改善をお願い。
# 設定
DB_NAME = 'repos.db'
BASE_URL = 'https://github.com/google?tab=repositories'
TARGET_PAGES = 1  # デモ用に最初の1ページのみスクレイピング（APIなしでのページネーションは複雑なため）

def init_db():
    """SQLiteデータベースを初期化する"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT,
            stars INTEGER
        )
    ''')
    conn.commit()
    return conn

def scrape_repos(conn):
    """リポジトリをスクレイピングしてDBに保存する"""
    cursor = conn.cursor()
    
    for page in range(1, TARGET_PAGES + 1):
        url = f"{BASE_URL}&page={page}"
        print(f"Scraping {url}...")
        
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 確実に存在する名前タグですべてのリポジトリ項目を見つける
        # これを基準に親の<li>や<div>を見つけることができる
        name_tags = soup.find_all('a', itemprop='name codeRepository')
        
        if not name_tags:
            print("No repositories found on this page.")
            break

        for name_tag in name_tags:
            repo_name = name_tag.get_text(strip=True)
            
            # 親の<li>を見つけて
            repo_item = name_tag.find_parent('li')
            
            if not repo_item:
                # 構造が異なる場合（例：divリスト）のフォールバック
                repo_item = name_tag.find_parent('div', class_='col-12') 

            if not repo_item:
                print(f"Could not find container for {repo_name}")
                continue

            # 言語
            lang_tag = repo_item.find('span', itemprop='programmingLanguage')
            language = lang_tag.get_text(strip=True) if lang_tag else "Unknown"
            
            # スター数
            # /stargazers で終わるリンクを探す
            star_tag = repo_item.find('a', href=lambda x: x and x.endswith('/stargazers'))
            stars_count = 0
            
            if star_tag:
                # まずテキストを取得してみる
                stars_text = star_tag.get_text(strip=True).replace(',', '')
                if not stars_text and star_tag.has_attr('aria-label'):
                     # フォールバックとして aria-label "455 stars" を使用
                     stars_text = star_tag['aria-label'].split(' ')[0].replace(',', '')
                
                if stars_text:
                    if 'k' in stars_text.lower():
                        try:
                            stars_count = int(float(stars_text.lower().replace('k', '')) * 1000)
                        except ValueError:
                            stars_count = 0
                    else:
                        try:
                            stars_count = int(stars_text)
                        except ValueError:
                            stars_count = 0
            
            print(f"  Found: {repo_name} | {language} | {stars_count}")

            # DBに挿入
            cursor.execute('''
                INSERT INTO repositories (name, language, stars)
                VALUES (?, ?, ?)
            ''', (repo_name, language, stars_count))
        
        conn.commit()
        
        # 要件: 1秒待機する
        time.sleep(1)

def display_data(conn):
    """DBからデータを選択して表示する"""
    cursor = conn.cursor()
    print("\n--- Database Contents (SELECT * FROM repositories) ---")
    cursor.execute("SELECT * FROM repositories")
    rows = cursor.fetchall()
    
    print(f"{'ID':<5} {'Name':<40} {'Language':<20} {'Stars':<10}")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<40} {row[2]:<20} {row[3]:<10}")

def main():
    conn = init_db()
    
    # 新規実行のために既存データを削除
    conn.execute("DELETE FROM repositories")
    conn.commit()
    
    scrape_repos(conn)
    display_data(conn)
    conn.close()

if __name__ == "__main__":
    main()
