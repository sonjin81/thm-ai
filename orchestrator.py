import os
import yaml
import re
from anthropic import Anthropic
from dotenv import load_dotenv

# 提示されたモジュールをインポート
from browser import THMManager
from terminal import execute_command, get_vpn_ip

load_dotenv()

class THMOrchestrator:
    def __init__(self, room_name):
        self.room_name = room_name
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.lhost = get_vpn_ip('tun0')
        self.manager = THMManager()
        self.step = 1
        self.history = []
        
        with open("prompts.yaml", "r") as f:
            self.config = yaml.safe_load(f)

    def parse_claude_response(self, text):
        """Claudeの回答から思考とコマンドを抽出"""
        thought = re.search(r"THOUGHT:\s*(.*)", text)
        command = re.search(r"COMMAND:\s*(.*)", text)
        return (thought.group(1) if thought else "", 
                command.group(1) if command else None)

    def run(self):
        # 1. 部屋の準備と情報の取得
        target_ip, room_context = self.manager.prepare_room(self.room_name)
        print(f"[*] Target IP: {target_ip}")
        print(f"[*] LHOST: {self.lhost}")

        current_context = f"Target IP: {target_ip}\nRoom Info: {room_context}"
        
        # 2. 攻略ループ (最大15ステップ)
        final_writeup = f"# Write-up: {self.room_name}\n\n"
        
        while self.step <= 15:
            print(f"\n--- Step {self.step} ---")
            
            # Claudeに次の行動を訊く
            system_prompt = self.config['system_instruction'].format(
                lhost=self.lhost, step_num=self.step
            )
            
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                system=system_prompt,
                messages=self.history + [{"role": "user", "content": current_context}]
            )
            
            content = response.content[0].text
            thought, command = self.parse_claude_response(content)
            
            print(f"💭 {thought}")
            
            if not command:
                print("[!] コマンドが提案されなかったため終了します。")
                final_writeup += content
                break

            # 3. コマンド実行と画像生成
            result = execute_command(command, self.step)
            
            # ログを履歴に追加
            self.history.append({"role": "user", "content": f"Result of step {self.step}:\n{result}"})
            final_writeup += f"{content}\n\n"
            
            # フラグが見つかったか確認
            if "thm{" in result.lower():
                print("[+] Flag detected!")
                
            self.step += 1

        # 4. 最終保存
        os.makedirs("writeups", exist_ok=True)
        with open(f"writeups/{self.room_name}.md", "w") as f:
            f.write(final_writeup)
        print(f"✅ Write-up saved to writeups/{self.room_name}.md")

if __name__ == "__main__":
    room = input("Enter Room Name (e.g., rootme): ")
    orchestrator = THMOrchestrator(room)
    orchestrator.run()
