import flet as ft
import requests
import json
from typing import Dict, List, Optional


class WeatherApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "気象庁天気予報アプリ"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.padding = 20
        self.page.bgcolor = "#0a0a0a"  # ダーク背景
        
        # カラーパレット（デジタル・電子的）
        self.colors = {
            "bg": "#0a0a0a",
            "bg_secondary": "#1a1a1a",
            "accent": "#00ffff",  # シアン
            "accent_secondary": "#00ff88",  # グリーン
            "text": "#00ff00",  # グリーン
            "text_secondary": "#00ffff",  # シアン
            "border": "#00ffff",
            "error": "#ff0066"
        }
        
        # 地域データのキャッシュ
        self.area_data: Optional[Dict] = None
        self.area_list: List[Dict] = []
        
        # UIコンポーネント
        self.area_dropdown = ft.Dropdown(
            label="地域を選択してください",
            width=400,
            options=[],
            on_change=self.on_area_selected,
            bgcolor=self.colors["bg_secondary"],
            color=self.colors["text"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["accent"],
            label_style=ft.TextStyle(color=self.colors["text_secondary"]),
            text_style=ft.TextStyle(color=self.colors["text"], font_family="monospace")
        )
        
        self.weather_info = ft.Column(
            controls=[],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )
        
        self.loading_indicator = ft.ProgressRing(
            visible=False,
            color=self.colors["accent"],
            stroke_width=3
        )
        self.error_message = ft.Text(
            "",
            color=self.colors["error"],
            visible=False,
            font_family="monospace",
            size=12
        )
        
        # レイアウト構築
        self.build_ui()
        
        # 初期データ読み込み
        self.load_area_list()
    
    def build_ui(self):
        """UIを構築"""
        # タイトル（デジタル風）
        title = ft.Container(
            content=ft.Text(
                "> WEATHER FORECAST SYSTEM <",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=self.colors["accent"],
                font_family="monospace"
            ),
            padding=ft.padding.only(bottom=10)
        )
        
        # セパレータ（デジタル風）
        separator = ft.Container(
            content=ft.Text(
                "=" * 60,
                color=self.colors["border"],
                font_family="monospace",
                size=12
            ),
            padding=ft.padding.symmetric(vertical=10)
        )
        
        # 天気情報表示エリア（デジタル風のボーダー）
        weather_container = ft.Container(
            content=ft.Container(
                content=self.weather_info,
                padding=15,
            ),
            width=700,
            height=450,
            bgcolor=self.colors["bg_secondary"],
            border=ft.border.all(2, self.colors["border"]),
            border_radius=0,
            padding=2,
            # グリッド背景効果をシミュレート
        )
        
        self.page.add(
            ft.Column(
                controls=[
                    title,
                    separator,
                    ft.Row(
                        controls=[self.area_dropdown, self.loading_indicator],
                        spacing=10
                    ),
                    self.error_message,
                    ft.Container(
                        content=ft.Text(
                            "> FORECAST DATA <",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=self.colors["accent_secondary"],
                            font_family="monospace"
                        ),
                        padding=ft.padding.only(top=15, bottom=5)
                    ),
                    weather_container
                ],
                spacing=5
            )
        )
    
    def load_area_list(self):
        """地域リストを取得"""
        self.loading_indicator.visible = True
        self.error_message.visible = False
        self.page.update()
        
        try:
            response = requests.get(
                "http://www.jma.go.jp/bosai/common/const/area.json",
                timeout=10
            )
            response.raise_for_status()
            self.area_data = response.json()
            
            # 地域リストを構築（centersから主要な地域を取得）
            self.area_list = []
            if "centers" in self.area_data:
                for center_code, center_info in self.area_data["centers"].items():
                    if "name" in center_info:
                        self.area_list.append({
                            "code": center_code,
                            "name": center_info["name"],
                            "type": "center"
                        })
            
            # オフィス（都道府県）も追加
            if "offices" in self.area_data:
                for office_code, office_info in self.area_data["offices"].items():
                    if "name" in office_info:
                        self.area_list.append({
                            "code": office_code,
                            "name": office_info["name"],
                            "type": "office"
                        })
            
            # ドロップダウンに追加
            self.area_dropdown.options = [
                ft.dropdown.Option(
                    key=area["code"],
                    text=f"{area['name']} ({area['code']})"
                )
                for area in sorted(self.area_list, key=lambda x: x["name"])
            ]
            
            self.loading_indicator.visible = False
            self.page.update()
            
        except requests.exceptions.RequestException as e:
            self.loading_indicator.visible = False
            self.error_message.value = f"[ERROR] FAILED TO LOAD AREA LIST: {str(e)}"
            self.error_message.visible = True
            self.page.update()
    
    def on_area_selected(self, e):
        """地域が選択された時の処理"""
        if not self.area_dropdown.value:
            return
        
        area_code = self.area_dropdown.value
        self.load_weather_info(area_code)
    
    def load_weather_info(self, area_code: str):
        """天気情報を取得"""
        self.loading_indicator.visible = True
        self.error_message.visible = False
        self.weather_info.controls.clear()
        self.page.update()
        
        try:
            url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            weather_data = response.json()
            
            # 天気情報を表示
            self.display_weather_info(weather_data)
            
            self.loading_indicator.visible = False
            self.page.update()
            
        except requests.exceptions.RequestException as e:
            self.loading_indicator.visible = False
            self.error_message.value = f"[ERROR] FAILED TO LOAD WEATHER DATA: {str(e)}"
            self.error_message.visible = True
            self.weather_info.controls.clear()
            self.page.update()
    
    def display_weather_info(self, weather_data: List[Dict]):
        """天気情報をUIに表示"""
        self.weather_info.controls.clear()
        
        if not weather_data:
            self.weather_info.controls.append(
                ft.Text(
                    "[ERROR] NO DATA AVAILABLE",
                    color=self.colors["error"],
                    font_family="monospace",
                    size=14
                )
            )
            return
        
        for area_forecast in weather_data:
            # エリア情報（デジタル風）
            if "area" in area_forecast:
                area_name = area_forecast.get("area", {}).get("name", "不明")
                self.weather_info.controls.append(
                    ft.Container(
                        content=ft.Text(
                            f">> {area_name} <<",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=self.colors["accent"],
                            font_family="monospace"
                        ),
                        padding=ft.padding.only(bottom=5)
                    )
                )
            
            # 発表時刻（デジタル時計風）
            if "reportDatetime" in area_forecast:
                report_time = area_forecast["reportDatetime"]
                self.weather_info.controls.append(
                    ft.Container(
                        content=ft.Text(
                            f"[TIME] {report_time}",
                            size=11,
                            color=self.colors["text_secondary"],
                            font_family="monospace"
                        ),
                        padding=ft.padding.only(bottom=8)
                    )
                )
            
            # 時系列予報
            if "timeSeries" in area_forecast:
                for time_series in area_forecast["timeSeries"]:
                    # 時間定義
                    if "timeDefines" in time_series:
                        time_defines = time_series["timeDefines"]
                        
                        # 天気予報
                        if "areas" in time_series:
                            for area_info in time_series["areas"]:
                                area_name = area_info.get("area", {}).get("name", "")
                                
                                # 天気コード
                                if "weatherCodes" in area_info:
                                    weather_codes = area_info["weatherCodes"]
                                    self.weather_info.controls.append(
                                        ft.Container(
                                            content=ft.Text(
                                                f"[FORECAST] {area_name}",
                                                size=13,
                                                weight=ft.FontWeight.BOLD,
                                                color=self.colors["accent_secondary"],
                                                font_family="monospace"
                                            ),
                                            padding=ft.padding.only(top=5, bottom=3)
                                        )
                                    )
                                    
                                    for i, (time_def, weather_code) in enumerate(zip(time_defines, weather_codes)):
                                        weather_text = self.get_weather_text(weather_code)
                                        # 日付を表示（timeDefinesは日付のみなので、日付部分を抽出）
                                        if "T" in time_def:
                                            date_part = time_def.split("T")[0]
                                            # 日付を短縮表示（例：2024-01-01 → 01/01）
                                            date_short = "/".join(date_part.split("-")[1:3]) if "-" in date_part else date_part
                                        else:
                                            date_short = time_def[:10] if len(time_def) >= 10 else time_def
                                        
                                        # インデックスベースの表示（DAY 1, DAY 2など）
                                        day_label = f"DAY {i+1}"
                                        self.weather_info.controls.append(
                                            ft.Container(
                                                content=ft.Text(
                                                    f"  [{day_label:6s}] {date_short} | {weather_text:20s} [CODE:{weather_code}]",
                                                    size=11,
                                                    color=self.colors["text"],
                                                    font_family="monospace"
                                                ),
                                                padding=ft.padding.only(left=10, bottom=2)
                                            )
                                        )
                                
                                # 気温（デジタル風）
                                if "temps" in area_info:
                                    temps = area_info["temps"]
                                    if temps:
                                        temp_values = [f"{temp:>3}°C" if temp else "  -" for temp in temps]
                                        temp_text = " | ".join(temp_values)
                                        self.weather_info.controls.append(
                                            ft.Container(
                                                content=ft.Text(
                                                    f"  [TEMP] {temp_text}",
                                                    size=11,
                                                    color=self.colors["text_secondary"],
                                                    font_family="monospace"
                                                ),
                                                padding=ft.padding.only(left=10, bottom=2)
                                            )
                                        )
                                
                                # 風速・風向（デジタル風）
                                if "winds" in area_info:
                                    winds = area_info["winds"]
                                    if winds:
                                        wind_text = " | ".join([wind if wind else "  -" for wind in winds])
                                        self.weather_info.controls.append(
                                            ft.Container(
                                                content=ft.Text(
                                                    f"  [WIND] {wind_text}",
                                                    size=11,
                                                    color=self.colors["text"],
                                                    font_family="monospace"
                                                ),
                                                padding=ft.padding.only(left=10, bottom=2)
                                            )
                                        )
                                
                                # 波の高さ（デジタル風）
                                if "waves" in area_info:
                                    waves = area_info["waves"]
                                    if waves:
                                        wave_text = " | ".join([wave if wave else "  -" for wave in waves])
                                        self.weather_info.controls.append(
                                            ft.Container(
                                                content=ft.Text(
                                                    f"  [WAVE] {wave_text}",
                                                    size=11,
                                                    color=self.colors["text"],
                                                    font_family="monospace"
                                                ),
                                                padding=ft.padding.only(left=10, bottom=2)
                                            )
                                        )
            
            # セパレータ（デジタル風）
            self.weather_info.controls.append(
                ft.Container(
                    content=ft.Text(
                        "-" * 50,
                        color=self.colors["border"],
                        font_family="monospace",
                        size=10
                    ),
                    padding=ft.padding.symmetric(vertical=8)
                )
            )
        
        if not self.weather_info.controls:
            self.weather_info.controls.append(
                ft.Text(
                    "[WARNING] NO DISPLAYABLE DATA",
                    color=self.colors["error"],
                    font_family="monospace",
                    size=12
                )
            )
    
    def get_weather_text(self, weather_code: str) -> str:
        """天気コードから天気の説明を取得"""
        weather_map = {
            "100": "晴れ",
            "101": "晴れ時々曇り",
            "102": "晴れ一時雨",
            "103": "晴れ時々雨",
            "104": "晴れ一時雪",
            "105": "晴れ時々雪",
            "106": "晴れ一時雨か雪",
            "107": "晴れ時々雨か雪",
            "108": "晴れ一時雨か雷雨",
            "110": "晴れ後時々曇り",
            "111": "晴れ後曇り",
            "112": "晴れ後一時雨",
            "113": "晴れ後時々雨",
            "114": "晴れ後雨",
            "115": "晴れ後一時雪",
            "116": "晴れ後時々雪",
            "117": "晴れ後雪",
            "118": "晴れ後雨か雪",
            "119": "晴れ後雨か雷雨",
            "120": "晴れ朝夕一時雨",
            "121": "晴れ朝の内一時雨",
            "122": "晴れ夕方一時雨",
            "123": "晴れ山沿い雷雨",
            "124": "晴れ山沿い雪",
            "125": "晴れ午後は雷雨",
            "126": "晴れ午後は雪",
            "130": "朝の内霧後晴れ",
            "131": "晴れ明け方霧",
            "132": "晴れ朝夕曇り",
            "140": "晴れ時々雨で雷を伴う",
            "200": "曇り",
            "201": "曇り時々晴れ",
            "202": "曇り一時雨",
            "203": "曇り時々雨",
            "204": "曇り一時雪",
            "205": "曇り時々雪",
            "206": "曇り一時雨か雪",
            "207": "曇り時々雨か雪",
            "208": "曇り一時雨か雷雨",
            "209": "霧",
            "210": "曇り後時々晴れ",
            "211": "曇り後晴れ",
            "212": "曇り後一時雨",
            "213": "曇り後時々雨",
            "214": "曇り後雨",
            "215": "曇り後一時雪",
            "216": "曇り後時々雪",
            "217": "曇り後雪",
            "218": "曇り後雨か雪",
            "219": "曇り後雨か雷雨",
            "220": "曇り朝夕一時雨",
            "221": "曇り朝の内一時雨",
            "222": "曇り夕方一時雨",
            "223": "曇り日中時々晴れ",
            "224": "曇り昼頃から雨",
            "225": "曇り夕方から雨",
            "226": "曇り夜は雨",
            "227": "曇り夜半から雨",
            "228": "曇り昼頃から雪",
            "229": "曇り夕方から雪",
            "230": "曇り夜は雪",
            "231": "曇り海上海岸は霧か霧雨",
            "300": "雨",
            "301": "雨時々晴れ",
            "302": "雨時々止む",
            "303": "雨時々雪",
            "304": "雨か雪",
            "306": "大雨",
            "308": "雨で暴風を伴う",
            "309": "雨一時雪",
            "311": "雨後晴れ",
            "313": "雨後曇り",
            "314": "雨後時々雪",
            "315": "雨後雪",
            "316": "雨か雪後晴れ",
            "317": "雨か雪後曇り",
            "320": "朝の内雨後晴れ",
            "321": "朝の内雨後曇り",
            "322": "雨朝晩一時雪",
            "323": "雨昼頃から晴れ",
            "324": "雨夕方から晴れ",
            "325": "雨夜は晴れ",
            "326": "雨夕方から雪",
            "327": "雨夜は雪",
            "328": "雨一時強く降る",
            "329": "雨一時みぞれ",
            "340": "雪か雨",
            "350": "雨で雷を伴う",
            "361": "雪か雨後晴れ",
            "371": "雪か雨後曇り",
            "400": "雪",
            "401": "雪時々晴れ",
            "402": "雪時々止む",
            "403": "雪時々雨",
            "405": "大雪",
            "406": "風雪強い",
            "407": "暴風雪",
            "409": "雪一時雨",
            "411": "雪後晴れ",
            "413": "雪後曇り",
            "414": "雪後雨",
            "420": "朝の内雪後晴れ",
            "421": "朝の内雪後曇り",
            "422": "雪昼頃から雨",
            "423": "雪夕方から雨",
            "425": "雪一時強く降る",
            "426": "雪後みぞれ",
            "427": "雪一時みぞれ",
            "450": "雪で雷を伴う",
        }
        return weather_map.get(weather_code, f"不明({weather_code})")


def main(page: ft.Page):
    app = WeatherApp(page)


if __name__ == "__main__":
    ft.app(target=main)

