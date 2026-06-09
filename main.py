import os, yaml, re, sys
from anthropic import Anthropic
from dotenv import load_dotenv
from browser import THMManager
from terminal import execute_command, get_vpn_ip

load_dotenv()

class ProfessionalTHMOrchestrator:
    def __init__(self, room_name):
        self.lhost = self._get_best_ip()
        # 制御文字を完全に排除
        self.room_name = "".join(c for c in room_name if c.isprintable()).strip()
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.manager = THMManager()
        self.history = []
        with open("prompts.yaml", "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)

    def _get_best_ip(self):
        for iface in ['tun0', 'tun1', 'eth0']:
            ip = get_vpn_ip(iface)
            if ip != "127.0.0.1": return ip
        return "127.0.0.1"

    def run(self):
        target_ip, room_struct = self.manager.prepare_room(self.room_name)
        if not target_ip:
            return print("[-] IP取得に失敗しました。VPN接続やボタンの状態を確認してください。")

        print(f"[*] 攻略フェーズ開始: {target_ip} / LHOST: {self.lhost}")
        
        step = 1
        current_context = f"Target: {target_ip}\nRoom Context: {room_struct}"
        
        while step <= 15:
            sys_msg = self.prompts['system_instruction'].format(target_ip=target_ip, lhost=self.lhost)
            response = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=3000,
                system=sys_msg,
                messages=self.history + [{"role": "user", "content": current_context}]
            )
            reply = response.content[0].text
            command = re.search(r"COMMAND:\s*(.*)", reply)
            if not command: break

            print(f"\n[Step {step}] {reply.split('COMMAND:')[0].strip()}")
            result = execute_command(command.group(1).strip(), step)
            
            self.history.append({"role": "assistant", "content": reply})
            self.history.append({"role": "user", "content": f"RESULT (Step {step}):\n{result}"})
            step += 1

        print("\n[*] 最終Write-up執筆中...")
        final_prompt = self.prompts['final_writeup_instruction'].format(room_name=self.room_name)
        
        writer_res = self.client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8000,
            system=final_prompt,
            messages=self.history + [{"role": "user", "content": f"正式構造: {room_struct}\nタスク順に美しく整理して。"}]
        )

        os.makedirs("writeups", exist_ok=True)
        path = f"writeups/{self.room_name}_complete.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(writer_res.content[0].text)
        print(f"✨ Write-upを保存しました: {path}")

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else input("Room Name: ")
    ProfessionalTHMOrchestrator(name).run()
