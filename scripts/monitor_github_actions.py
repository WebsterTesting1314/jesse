#!/usr/bin/env python3
"""
GitHub Actions 工作流程監控腳本
監控 CI/CD 執行狀況並提供詳細日誌分析
"""

import time
import requests
import json
from datetime import datetime, timedelta
import subprocess
import sys


class GitHubActionsMonitor:
    """GitHub Actions 監控器"""
    
    def __init__(self, repo_owner, repo_name):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = "https://api.github.com"
        
    def get_workflow_runs(self, workflow_id=None, limit=10):
        """獲取工作流程執行記錄"""
        if workflow_id:
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        
        params = {"per_page": limit}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API 請求失敗: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 網路錯誤: {e}")
            return None
    
    def get_workflow_jobs(self, run_id):
        """獲取工作流程中的作業詳情"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/jobs"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 無法獲取作業詳情: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 獲取作業詳情時發生錯誤: {e}")
            return None
    
    def get_job_logs(self, job_id):
        """獲取作業日誌"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/actions/jobs/{job_id}/logs"
        
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                return response.text
            else:
                print(f"❌ 無法獲取日誌: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 獲取日誌時發生錯誤: {e}")
            return None
    
    def format_duration(self, start_time, end_time):
        """格式化執行時間"""
        if not start_time or not end_time:
            return "N/A"
        
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = end - start
        
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def get_status_emoji(self, status, conclusion):
        """獲取狀態表情符號"""
        if status == "in_progress":
            return "🔄"
        elif status == "queued":
            return "⏳"
        elif conclusion == "success":
            return "✅"
        elif conclusion == "failure":
            return "❌"
        elif conclusion == "cancelled":
            return "🚫"
        elif conclusion == "skipped":
            return "⏭️"
        else:
            return "❓"
    
    def monitor_latest_run(self, check_interval=30, max_wait_time=1800):
        """監控最新的工作流程執行"""
        print("🔍 開始監控 GitHub Actions 工作流程執行...")
        print(f"📍 倉庫: {self.repo_owner}/{self.repo_name}")
        print(f"⏰ 檢查間隔: {check_interval}秒")
        print(f"⏱️ 最大等待時間: {max_wait_time}秒 ({max_wait_time//60}分鐘)")
        print("=" * 80)
        
        start_monitor_time = time.time()
        last_run_id = None
        
        while time.time() - start_monitor_time < max_wait_time:
            # 獲取最新的工作流程執行
            runs_data = self.get_workflow_runs(limit=5)
            
            if not runs_data or not runs_data.get('workflow_runs'):
                print("❌ 無法獲取工作流程資料")
                time.sleep(check_interval)
                continue
            
            latest_run = runs_data['workflow_runs'][0]
            run_id = latest_run['id']
            
            # 如果發現新的執行
            if last_run_id != run_id:
                last_run_id = run_id
                print(f"\n🆕 發現新的工作流程執行:")
                self.display_run_summary(latest_run)
            
            # 檢查當前執行狀態
            if latest_run['status'] in ['in_progress', 'queued']:
                print(f"\n📊 工作流程執行中... (檢查時間: {datetime.now().strftime('%H:%M:%S')})")
                self.display_run_details(latest_run)
                
                # 獲取作業詳情
                jobs_data = self.get_workflow_jobs(run_id)
                if jobs_data and jobs_data.get('jobs'):
                    self.display_jobs_summary(jobs_data['jobs'])
                
                time.sleep(check_interval)
            else:
                # 工作流程已完成
                print(f"\n🏁 工作流程執行完成!")
                self.display_run_details(latest_run)
                
                # 獲取最終作業結果
                jobs_data = self.get_workflow_jobs(run_id)
                if jobs_data and jobs_data.get('jobs'):
                    print(f"\n📋 最終作業結果:")
                    self.display_jobs_summary(jobs_data['jobs'])
                    
                    # 分析失敗的作業
                    failed_jobs = [job for job in jobs_data['jobs'] if job['conclusion'] == 'failure']
                    if failed_jobs:
                        print(f"\n💥 失敗的作業分析:")
                        for job in failed_jobs:
                            self.analyze_failed_job(job)
                
                # 生成總結報告
                self.generate_final_report(latest_run, jobs_data.get('jobs', []) if jobs_data else [])
                break
        else:
            print(f"\n⏰ 監控超時 ({max_wait_time//60}分鐘)")
    
    def display_run_summary(self, run):
        """顯示執行摘要"""
        emoji = self.get_status_emoji(run['status'], run.get('conclusion'))
        print(f"{emoji} 工作流程: {run['name']}")
        print(f"🔗 執行 ID: {run['id']}")
        print(f"🌿 分支: {run['head_branch']}")
        print(f"💬 提交: {run['head_commit']['message'][:100]}...")
        print(f"👤 觸發者: {run['triggering_actor']['login']}")
        print(f"📅 開始時間: {run['created_at']}")
        
        if run.get('updated_at'):
            duration = self.format_duration(run['created_at'], run['updated_at'])
            print(f"⏱️ 執行時間: {duration}")
    
    def display_run_details(self, run):
        """顯示執行詳情"""
        emoji = self.get_status_emoji(run['status'], run.get('conclusion'))
        print(f"{emoji} 狀態: {run['status']}")
        
        if run.get('conclusion'):
            print(f"🎯 結果: {run['conclusion']}")
        
        print(f"🔗 查看詳情: {run['html_url']}")
    
    def display_jobs_summary(self, jobs):
        """顯示作業摘要"""
        print(f"\n📊 作業狀態 ({len(jobs)} 個作業):")
        print("-" * 60)
        
        for job in jobs:
            emoji = self.get_status_emoji(job['status'], job.get('conclusion'))
            duration = self.format_duration(job.get('started_at'), job.get('completed_at'))
            
            print(f"{emoji} {job['name']:<40} | {job['status']:<12} | {duration}")
    
    def analyze_failed_job(self, job):
        """分析失敗的作業"""
        print(f"\n❌ 失敗作業: {job['name']}")
        print(f"🔗 日誌連結: {job['html_url']}")
        
        # 嘗試獲取日誌
        logs = self.get_job_logs(job['id'])
        if logs:
            # 提取錯誤信息
            error_lines = []
            lines = logs.split('\n')
            
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception', '❌']):
                    # 包含前後幾行以提供上下文
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    error_lines.extend(lines[start:end])
                    error_lines.append("-" * 40)
            
            if error_lines:
                print(f"📝 錯誤摘要:")
                for line in error_lines[-20:]:  # 顯示最後20行錯誤
                    print(f"   {line}")
        else:
            print("❌ 無法獲取詳細日誌")
    
    def generate_final_report(self, run, jobs):
        """生成最終報告"""
        print(f"\n" + "=" * 80)
        print(f"📊 工作流程執行總結報告")
        print(f"=" * 80)
        
        emoji = self.get_status_emoji(run['status'], run.get('conclusion'))
        print(f"{emoji} 整體狀態: {run.get('conclusion', run['status'])}")
        
        total_duration = self.format_duration(run['created_at'], run.get('updated_at'))
        print(f"⏱️ 總執行時間: {total_duration}")
        
        # 統計作業結果
        success_count = len([j for j in jobs if j.get('conclusion') == 'success'])
        failure_count = len([j for j in jobs if j.get('conclusion') == 'failure'])
        skipped_count = len([j for j in jobs if j.get('conclusion') == 'skipped'])
        
        print(f"📈 作業統計:")
        print(f"   ✅ 成功: {success_count}")
        print(f"   ❌ 失敗: {failure_count}")
        print(f"   ⏭️ 跳過: {skipped_count}")
        print(f"   📊 總計: {len(jobs)}")
        
        # 建議
        print(f"\n💡 建議:")
        if failure_count == 0:
            print("   🎉 所有測試通過！系統準備就緒。")
            print("   🚀 可以考慮部署到測試環境。")
        else:
            print("   🔧 需要修復失敗的作業。")
            print("   📖 查看上方的錯誤分析以了解詳情。")
            print("   🔄 修復後重新執行工作流程。")
        
        print(f"\n🔗 完整報告: {run['html_url']}")
        print(f"=" * 80)


def main():
    """主函數"""
    # 從 git remote 獲取倉庫信息
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                               capture_output=True, text=True, check=True)
        remote_url = result.stdout.strip()
        
        # 解析 GitHub 倉庫信息
        if 'github.com' in remote_url:
            # 支持 HTTPS 和 SSH URL
            if remote_url.startswith('https://'):
                # https://github.com/owner/repo.git
                parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
            else:
                # git@github.com:owner/repo.git
                parts = remote_url.split(':')[1].replace('.git', '').split('/')
            
            if len(parts) >= 2:
                repo_owner = parts[0]
                repo_name = parts[1]
            else:
                raise ValueError("無法解析倉庫信息")
        else:
            raise ValueError("不是 GitHub 倉庫")
            
    except Exception as e:
        print(f"❌ 無法獲取倉庫信息: {e}")
        print("💡 請確保在 git 倉庫目錄中執行此腳本")
        sys.exit(1)
    
    print(f"🎯 監控目標: {repo_owner}/{repo_name}")
    
    # 建立監控器
    monitor = GitHubActionsMonitor(repo_owner, repo_name)
    
    # 開始監控
    monitor.monitor_latest_run(
        check_interval=30,      # 每30秒檢查一次
        max_wait_time=1800      # 最多等待30分鐘
    )


if __name__ == "__main__":
    main()