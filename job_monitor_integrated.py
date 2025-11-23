"""
INTEGRATED Job Monitor System
1. Finds jobs matching your criteria
2. Intelligently auto-applies using your profile
3. Finds 2 relevant people to network with after applying
"""

import time
import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import logging
from auto_apply_enhanced import EnhancedAutoApply, load_profile
from linkedin_network_finder import LinkedInNetworkFinder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_monitor_integrated.log'),
        logging.StreamHandler()
    ]
)

class IntegratedJobMonitor:
    def __init__(self, config_file='config.json', profile_file='profile.json'):
        """Initialize with configuration and profile"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.profile = load_profile(profile_file)
        
        self.keywords = self.config['keywords']
        self.locations = self.config['locations']
        self.companies_to_monitor = self.config['companies_to_monitor']
        self.auto_apply = self.config['auto_apply']
        self.find_networking_contacts = self.config.get('find_networking_contacts', True)
        self.linkedin_email = self.config.get('linkedin_email', '')
        self.linkedin_password = self.config.get('linkedin_password', '')
        
        # Setup Chrome options
        self.chrome_options = Options()
        if not self.config.get('show_browser', False):
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Initialize tracking
        self.jobs_found = []
        self.jobs_applied = []
        self.networking_contacts = []
        
    def start_driver(self):
        """Start Chrome driver"""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Initialize enhanced modules
        self.auto_applier = EnhancedAutoApply(self.driver, self.profile)
        self.network_finder = LinkedInNetworkFinder(self.driver, self.profile)
        
        logging.info("Chrome driver started with enhanced features")
        
    def close_driver(self):
        """Close Chrome driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logging.info("Chrome driver closed")
    
    def login_linkedin(self):
        """Login to LinkedIn"""
        try:
            logging.info("Logging into LinkedIn...")
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(2)
            
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.linkedin_email)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.linkedin_password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(3)
            logging.info("LinkedIn login successful")
            return True
            
        except Exception as e:
            logging.error(f"LinkedIn login failed: {e}")
            return False
    
    def search_linkedin_jobs(self, keyword, location):
        """Search for jobs on LinkedIn"""
        try:
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_AL=true"
            logging.info(f"Searching LinkedIn: {keyword} in {location}")
            self.driver.get(search_url)
            time.sleep(3)
            
            # Scroll to load jobs
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Find job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job-card-container")
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title")
                    title = title_elem.text.strip()
                    job_url = title_elem.get_attribute('href')
                    
                    company_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-container__company-name")
                    company = company_elem.text.strip()
                    
                    location_elem = card.find_element(By.CSS_SELECTOR, "li.job-card-container__metadata-item")
                    job_location = location_elem.text.strip()
                    
                    # Check if it's Easy Apply
                    is_easy_apply = len(card.find_elements(By.CSS_SELECTOR, "li.job-card-container__apply-method")) > 0
                    
                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': job_url,
                        'source': 'LinkedIn',
                        'easy_apply': is_easy_apply,
                        'keyword': keyword,
                        'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'Found'
                    }
                    
                    # Check if already tracked
                    if not any(j['url'] == job_url for j in self.jobs_found):
                        self.jobs_found.append(job_data)
                        logging.info(f"New job found: {title} at {company}")
                        
                        # Auto-apply if enabled and it's Easy Apply
                        if self.auto_apply and is_easy_apply:
                            self.apply_and_network(job_data)
                
                except Exception as e:
                    logging.warning(f"Error parsing job card: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error searching LinkedIn: {e}")
    
    def apply_and_network(self, job_data):
        """
        INTEGRATED WORKFLOW:
        1. Apply to the job using enhanced auto-apply
        2. If successful, find 2 people to network with
        """
        try:
            logging.info(f"\n{'='*60}")
            logging.info(f"STARTING INTEGRATED APPLICATION WORKFLOW")
            logging.info(f"Job: {job_data['title']} at {job_data['company']}")
            logging.info(f"{'='*60}\n")
            
            # STEP 1: Apply to the job
            logging.info("STEP 1: Applying to job...")
            success, status = self.auto_applier.fill_linkedin_easy_apply(job_data['url'])
            
            job_data['status'] = status
            
            if success:
                self.jobs_applied.append(job_data)
                logging.info(f"✓ Application status: {status}")
                
                # STEP 2: Find networking contacts
                if self.find_networking_contacts:
                    logging.info("\nSTEP 2: Finding networking contacts...")
                    time.sleep(3)  # Brief pause
                    
                    people = self.network_finder.find_and_save_networking_contacts(job_data)
                    
                    if people:
                        self.networking_contacts.extend(people)
                        logging.info(f"✓ Found {len(people)} networking contacts")
                        
                        # Update job data with networking info
                        job_data['networking_contacts_found'] = len(people)
                        job_data['networking_contacts'] = [p['name'] for p in people]
                    else:
                        logging.warning("⚠ No networking contacts found")
                        job_data['networking_contacts_found'] = 0
                
                logging.info(f"\n{'='*60}")
                logging.info("WORKFLOW COMPLETE")
                logging.info(f"{'='*60}\n")
            else:
                logging.warning(f"⚠ Application unsuccessful: {status}")
            
            time.sleep(5)  # Rate limiting between applications
                
        except Exception as e:
            logging.error(f"Error in apply_and_network workflow: {e}")
            job_data['status'] = f'Error: {str(e)}'
    
    def save_results(self):
        """Save all results to CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save jobs found
        if self.jobs_found:
            df = pd.DataFrame(self.jobs_found)
            csv_file = f'jobs_found_{timestamp}.csv'
            df.to_csv(csv_file, index=False)
            logging.info(f"Saved {len(self.jobs_found)} jobs to {csv_file}")
            
            # Update master tracker
            try:
                master_df = pd.read_csv('job_tracker_master.csv')
                master_df = pd.concat([master_df, df]).drop_duplicates(subset=['url'], keep='last')
            except FileNotFoundError:
                master_df = df
            
            master_df.to_csv('job_tracker_master.csv', index=False)
            logging.info("Updated master job tracker")
        
        # Networking contacts are saved automatically by network_finder
        # But we can also create a summary
        if self.networking_contacts:
            logging.info(f"Total networking contacts found: {len(self.networking_contacts)}")
        
        # Save state
        with open('job_monitor_state.json', 'w') as f:
            json.dump({
                'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'jobs_found': len(self.jobs_found),
                'jobs_applied': len(self.jobs_applied),
                'networking_contacts': len(self.networking_contacts)
            }, f, indent=2)
    
    def run(self):
        """Main execution with integrated workflow"""
        try:
            self.start_driver()
            
            # Login to LinkedIn
            if self.linkedin_email and self.linkedin_password:
                if not self.login_linkedin():
                    logging.error("LinkedIn login required for auto-apply and networking features")
                    return
            else:
                logging.warning("No LinkedIn credentials - running in monitor-only mode")
            
            # Search LinkedIn for each keyword/location
            for keyword in self.keywords:
                for location in self.locations:
                    self.search_linkedin_jobs(keyword, location)
                    time.sleep(3)
            
            # Save all results
            self.save_results()
            
            # Print comprehensive summary
            self.print_summary()
            
        except Exception as e:
            logging.error(f"Error in main execution: {e}")
            
        finally:
            self.close_driver()
    
    def print_summary(self):
        """Print detailed summary of the run"""
        logging.info(f"\n{'='*70}")
        logging.info(f"INTEGRATED JOB MONITOR - FINAL SUMMARY")
        logging.info(f"{'='*70}")
        logging.info(f"")
        logging.info(f"📋 JOBS:")
        logging.info(f"  • Total jobs found: {len(self.jobs_found)}")
        logging.info(f"  • Applications submitted: {len(self.jobs_applied)}")
        logging.info(f"  • Success rate: {len(self.jobs_applied)/len(self.jobs_found)*100:.1f}%" if self.jobs_found else "  • Success rate: N/A")
        logging.info(f"")
        logging.info(f"🤝 NETWORKING:")
        logging.info(f"  • People identified for networking: {len(self.networking_contacts)}")
        logging.info(f"  • Average per job applied: {len(self.networking_contacts)/len(self.jobs_applied):.1f}" if self.jobs_applied else "  • Average per job: N/A")
        logging.info(f"")
        logging.info(f"📊 NEXT STEPS:")
        
        if self.jobs_applied:
            logging.info(f"  1. Review job_tracker_master.csv for applied jobs")
            logging.info(f"  2. Check networking_targets.csv for people to connect with")
            logging.info(f"  3. Send personalized connection requests on LinkedIn")
            logging.info(f"  4. Follow up on applications in 3-5 days")
        else:
            logging.info(f"  1. Review job_tracker_master.csv for found jobs")
            logging.info(f"  2. Manually apply to interesting positions")
            logging.info(f"  3. Consider enabling auto_apply in config.json")
        
        logging.info(f"")
        logging.info(f"{'='*70}\n")

if __name__ == "__main__":
    monitor = IntegratedJobMonitor()
    monitor.run()
