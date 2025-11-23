"""
Job Monitor & Auto-Apply System
Monitors LinkedIn and company career pages for trade operations roles
"""

import time
import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_monitor.log'),
        logging.StreamHandler()
    ]
)

class JobMonitor:
    def __init__(self, config_file='config.json'):
        """Initialize the job monitor with configuration"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.keywords = self.config['keywords']
        self.locations = self.config['locations']
        self.companies_to_monitor = self.config['companies_to_monitor']
        self.auto_apply = self.config['auto_apply']
        self.linkedin_email = self.config.get('linkedin_email', '')
        self.linkedin_password = self.config.get('linkedin_password', '')
        
        # Setup Chrome options
        self.chrome_options = Options()
        if not self.config.get('show_browser', False):
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Initialize results tracking
        self.jobs_found = []
        self.jobs_applied = []
        
    def start_driver(self):
        """Start Chrome driver"""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("Chrome driver started")
        
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
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
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
                            self.apply_to_job(job_data)
                
                except Exception as e:
                    logging.warning(f"Error parsing job card: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error searching LinkedIn: {e}")
    
    def apply_to_job(self, job_data):
        """Apply to a LinkedIn Easy Apply job"""
        try:
            logging.info(f"Attempting to apply: {job_data['title']}")
            self.driver.get(job_data['url'])
            time.sleep(2)
            
            # Click Easy Apply button
            easy_apply_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jobs-apply-button"))
            )
            easy_apply_button.click()
            time.sleep(2)
            
            # Handle multi-page application
            max_pages = 5
            for page in range(max_pages):
                try:
                    # Check if there's a Next button
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    
                    # Fill any required fields (basic implementation)
                    # You can expand this to handle specific questions
                    
                    next_button.click()
                    time.sleep(2)
                    
                except NoSuchElementException:
                    # Check for Submit/Review button
                    try:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                        
                        if self.config.get('confirm_before_submit', True):
                            logging.info(f"Ready to submit application for: {job_data['title']}")
                            logging.info("Set 'confirm_before_submit': false in config to auto-submit")
                            break
                        else:
                            submit_button.click()
                            time.sleep(2)
                            job_data['status'] = 'Applied'
                            self.jobs_applied.append(job_data)
                            logging.info(f"✓ Applied to: {job_data['title']}")
                            break
                            
                    except NoSuchElementException:
                        break
            
            # Close the modal
            try:
                close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Dismiss']")
                close_button.click()
            except:
                pass
                
        except Exception as e:
            logging.warning(f"Could not auto-apply to {job_data['title']}: {e}")
            job_data['status'] = 'Manual Application Required'
    
    def search_company_website(self, company_name, careers_url):
        """Search a company's career page"""
        try:
            logging.info(f"Checking {company_name} careers page...")
            self.driver.get(careers_url)
            time.sleep(3)
            
            # This is a generic scraper - you'd customize per company
            page_text = self.driver.page_source.lower()
            
            # Check if any keywords appear
            found_keywords = [k for k in self.keywords if k.lower() in page_text]
            
            if found_keywords:
                job_data = {
                    'title': f"Potential match at {company_name}",
                    'company': company_name,
                    'location': 'See website',
                    'url': careers_url,
                    'source': 'Company Website',
                    'easy_apply': False,
                    'keyword': ', '.join(found_keywords),
                    'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Manual Review Required'
                }
                
                if not any(j['url'] == careers_url for j in self.jobs_found):
                    self.jobs_found.append(job_data)
                    logging.info(f"Potential match found at {company_name}")
                    
        except Exception as e:
            logging.error(f"Error checking {company_name}: {e}")
    
    def save_results(self):
        """Save results to CSV and JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to CSV
        if self.jobs_found:
            df = pd.DataFrame(self.jobs_found)
            csv_file = f'jobs_found_{timestamp}.csv'
            df.to_csv(csv_file, index=False)
            logging.info(f"Saved {len(self.jobs_found)} jobs to {csv_file}")
            
            # Also append to master tracking file
            try:
                master_df = pd.read_csv('job_tracker_master.csv')
                master_df = pd.concat([master_df, df]).drop_duplicates(subset=['url'], keep='last')
            except FileNotFoundError:
                master_df = df
            
            master_df.to_csv('job_tracker_master.csv', index=False)
            logging.info("Updated master tracker")
        
        # Save to JSON for program state
        with open('job_monitor_state.json', 'w') as f:
            json.dump({
                'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'jobs_found': self.jobs_found,
                'jobs_applied': self.jobs_applied
            }, f, indent=2)
    
    def run(self):
        """Main execution loop"""
        try:
            self.start_driver()
            
            # Login to LinkedIn if credentials provided
            if self.linkedin_email and self.linkedin_password:
                if not self.login_linkedin():
                    logging.error("LinkedIn login required for auto-apply features")
                    return
            
            # Search LinkedIn for each keyword/location combo
            for keyword in self.keywords:
                for location in self.locations:
                    self.search_linkedin_jobs(keyword, location)
                    time.sleep(3)  # Rate limiting
            
            # Check company websites
            for company_name, careers_url in self.companies_to_monitor.items():
                self.search_company_website(company_name, careers_url)
                time.sleep(3)
            
            # Save results
            self.save_results()
            
            # Print summary
            logging.info(f"\n{'='*50}")
            logging.info(f"Job Monitor Summary")
            logging.info(f"{'='*50}")
            logging.info(f"Total jobs found: {len(self.jobs_found)}")
            logging.info(f"Jobs applied to: {len(self.jobs_applied)}")
            logging.info(f"Jobs requiring manual review: {len([j for j in self.jobs_found if j['status'] != 'Applied'])}")
            logging.info(f"{'='*50}\n")
            
        except Exception as e:
            logging.error(f"Error in main execution: {e}")
            
        finally:
            self.close_driver()

if __name__ == "__main__":
    monitor = JobMonitor()
    monitor.run()
