"""
Job Tracker Dashboard
View and manage your tracked jobs
"""

import pandas as pd
import os
from datetime import datetime
import json

class JobDashboard:
    def __init__(self):
        self.master_file = 'job_tracker_master.csv'
        self.load_data()
    
    def load_data(self):
        """Load job data"""
        try:
            self.df = pd.read_csv(self.master_file)
            self.df['found_date'] = pd.to_datetime(self.df['found_date'])
        except FileNotFoundError:
            print(f"❌ {self.master_file} not found. Run job_monitor.py first.")
            self.df = pd.DataFrame()
    
    def show_summary(self):
        """Show summary statistics"""
        if self.df.empty:
            return
        
        print("\n" + "=" * 70)
        print("JOB TRACKER DASHBOARD")
        print("=" * 70)
        print()
        
        # Overall stats
        print(f"📊 Total Jobs Tracked: {len(self.df)}")
        print(f"📅 Date Range: {self.df['found_date'].min().strftime('%Y-%m-%d')} to {self.df['found_date'].max().strftime('%Y-%m-%d')}")
        print()
        
        # Status breakdown
        print("Status Breakdown:")
        status_counts = self.df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"  • {status}: {count}")
        print()
        
        # Source breakdown
        print("Sources:")
        source_counts = self.df['source'].value_counts()
        for source, count in source_counts.items():
            print(f"  • {source}: {count}")
        print()
        
        # Top companies
        print("Top Companies:")
        company_counts = self.df['company'].value_counts().head(5)
        for company, count in company_counts.items():
            print(f"  • {company}: {count} jobs")
        print()
        
        # Easy Apply stats
        if 'easy_apply' in self.df.columns:
            easy_apply_count = self.df['easy_apply'].sum()
            print(f"⚡ Easy Apply Jobs: {easy_apply_count} ({easy_apply_count/len(self.df)*100:.1f}%)")
            print()
    
    def show_recent(self, n=10):
        """Show most recent jobs"""
        if self.df.empty:
            return
        
        print("=" * 70)
        print(f"RECENT JOBS (Last {n})")
        print("=" * 70)
        print()
        
        recent = self.df.nlargest(n, 'found_date')
        
        for idx, (_, job) in enumerate(recent.iterrows(), 1):
            print(f"{idx}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Found: {job['found_date'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Status: {job['status']}")
            if job.get('easy_apply', False):
                print(f"   ⚡ Easy Apply")
            print(f"   🔗 {job['url']}")
            print()
    
    def search_jobs(self, keyword):
        """Search jobs by keyword"""
        if self.df.empty:
            return
        
        mask = (
            self.df['title'].str.contains(keyword, case=False, na=False) |
            self.df['company'].str.contains(keyword, case=False, na=False) |
            self.df['keyword'].str.contains(keyword, case=False, na=False)
        )
        
        results = self.df[mask]
        
        print("\n" + "=" * 70)
        print(f"SEARCH RESULTS: '{keyword}' ({len(results)} found)")
        print("=" * 70)
        print()
        
        if results.empty:
            print("No jobs found matching that keyword.")
            return
        
        for idx, (_, job) in enumerate(results.iterrows(), 1):
            print(f"{idx}. {job['title']} at {job['company']}")
            print(f"   {job['location']} - {job['status']}")
            print(f"   {job['url']}")
            print()
    
    def show_by_company(self):
        """Show jobs grouped by company"""
        if self.df.empty:
            return
        
        print("\n" + "=" * 70)
        print("JOBS BY COMPANY")
        print("=" * 70)
        print()
        
        for company, group in self.df.groupby('company'):
            print(f"\n{company} ({len(group)} jobs):")
            print("-" * 50)
            
            for _, job in group.iterrows():
                status_emoji = "✓" if job['status'] == 'Applied' else "○"
                easy_emoji = "⚡" if job.get('easy_apply', False) else ""
                print(f"  {status_emoji} {job['title']} {easy_emoji}")
                print(f"    {job['location']} - {job['found_date'].strftime('%Y-%m-%d')}")
            print()
    
    def show_easy_apply_only(self):
        """Show only Easy Apply jobs"""
        if self.df.empty or 'easy_apply' not in self.df.columns:
            return
        
        easy_jobs = self.df[self.df['easy_apply'] == True]
        
        print("\n" + "=" * 70)
        print(f"⚡ EASY APPLY JOBS ({len(easy_jobs)} found)")
        print("=" * 70)
        print()
        
        if easy_jobs.empty:
            print("No Easy Apply jobs found.")
            return
        
        unapplied = easy_jobs[easy_jobs['status'] != 'Applied']
        
        if not unapplied.empty:
            print(f"🎯 {len(unapplied)} jobs you haven't applied to yet:")
            print()
            
            for idx, (_, job) in enumerate(unapplied.iterrows(), 1):
                print(f"{idx}. {job['title']}")
                print(f"   {job['company']} - {job['location']}")
                print(f"   {job['url']}")
                print()
    
    def export_to_excel(self, filename='job_tracker.xlsx'):
        """Export to Excel with formatting"""
        if self.df.empty:
            return
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main sheet
                self.df.to_excel(writer, sheet_name='All Jobs', index=False)
                
                # Summary sheet
                summary_data = {
                    'Metric': ['Total Jobs', 'Applied', 'Pending', 'Easy Apply'],
                    'Count': [
                        len(self.df),
                        len(self.df[self.df['status'] == 'Applied']),
                        len(self.df[self.df['status'] != 'Applied']),
                        len(self.df[self.df.get('easy_apply', False) == True])
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # By company
                company_summary = self.df.groupby('company').size().reset_index(name='Job Count')
                company_summary = company_summary.sort_values('Job Count', ascending=False)
                company_summary.to_excel(writer, sheet_name='By Company', index=False)
            
            print(f"\n✓ Exported to {filename}")
            
        except Exception as e:
            print(f"\n❌ Export failed: {e}")
    
    def interactive_menu(self):
        """Interactive menu"""
        while True:
            print("\n" + "=" * 70)
            print("JOB TRACKER MENU")
            print("=" * 70)
            print()
            print("1. Show Summary")
            print("2. Show Recent Jobs")
            print("3. Search Jobs")
            print("4. View by Company")
            print("5. Show Easy Apply Jobs Only")
            print("6. Export to Excel")
            print("7. Refresh Data")
            print("0. Exit")
            print()
            
            choice = input("Select option (0-7): ").strip()
            
            if choice == '1':
                self.show_summary()
            elif choice == '2':
                n = input("How many recent jobs? (default 10): ").strip()
                n = int(n) if n.isdigit() else 10
                self.show_recent(n)
            elif choice == '3':
                keyword = input("Enter search keyword: ").strip()
                if keyword:
                    self.search_jobs(keyword)
            elif choice == '4':
                self.show_by_company()
            elif choice == '5':
                self.show_easy_apply_only()
            elif choice == '6':
                filename = input("Export filename (default: job_tracker.xlsx): ").strip()
                filename = filename if filename else 'job_tracker.xlsx'
                self.export_to_excel(filename)
            elif choice == '7':
                self.load_data()
                print("\n✓ Data refreshed")
            elif choice == '0':
                print("\nGoodbye!")
                break
            else:
                print("\n❌ Invalid option")
            
            input("\nPress Enter to continue...")

def main():
    """Main function"""
    dashboard = JobDashboard()
    
    if dashboard.df.empty:
        print("\nNo job data found. Run job_monitor.py first to track jobs.")
        return
    
    # Show summary by default
    dashboard.show_summary()
    dashboard.show_recent(5)
    
    # Start interactive menu
    print("\n" + "=" * 70)
    response = input("Enter interactive mode? (y/n): ").strip().lower()
    if response == 'y':
        dashboard.interactive_menu()

if __name__ == "__main__":
    main()
