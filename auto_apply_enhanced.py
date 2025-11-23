"""
Enhanced Auto-Apply Module
Intelligently fills application forms with your profile data
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
import logging
import json

class EnhancedAutoApply:
    def __init__(self, driver, profile_data):
        """
        Initialize with driver and your profile data
        profile_data should contain all your info from profile.json
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.profile = profile_data
        
    def fill_text_field(self, field, value):
        """Fill a text field"""
        try:
            field.clear()
            field.send_keys(value)
            return True
        except Exception as e:
            logging.warning(f"Could not fill field: {e}")
            return False
    
    def handle_phone_number(self, field):
        """Smart phone number handler"""
        phone = self.profile.get('phone', '')
        # Remove formatting, LinkedIn prefers raw numbers
        phone_clean = ''.join(filter(str.isdigit, phone))
        self.fill_text_field(field, phone_clean)
    
    def handle_years_experience(self, field, question_text):
        """Calculate years of experience based on question"""
        # Map common question types to your experience
        experience_map = {
            'total': self.profile.get('total_years_experience', 3),
            'python': self.profile.get('python_years', 2),
            'finance': self.profile.get('finance_years', 3),
            'trading': self.profile.get('trading_years', 2),
            'operations': self.profile.get('operations_years', 2)
        }
        
        question_lower = question_text.lower()
        
        for key, years in experience_map.items():
            if key in question_lower:
                self.fill_text_field(field, str(years))
                return True
        
        # Default to total experience
        self.fill_text_field(field, str(experience_map['total']))
        return True
    
    def handle_dropdown(self, select_element, question_text):
        """Smart dropdown handler"""
        try:
            select = Select(select_element)
            options = [opt.text.lower() for opt in select.options]
            question_lower = question_text.lower()
            
            # Education level
            if 'education' in question_lower or 'degree' in question_lower:
                target = self.profile.get('education_level', 'bachelor').lower()
                for i, opt in enumerate(options):
                    if target in opt:
                        select.select_by_index(i)
                        return True
            
            # Work authorization
            if 'authorized' in question_lower or 'sponsorship' in question_lower:
                if self.profile.get('work_authorized', True):
                    for i, opt in enumerate(options):
                        if 'yes' in opt or 'authorized' in opt:
                            select.select_by_index(i)
                            return True
            
            # Visa status
            if 'visa' in question_lower:
                visa_status = self.profile.get('visa_status', 'citizen').lower()
                for i, opt in enumerate(options):
                    if visa_status in opt or 'citizen' in opt:
                        select.select_by_index(i)
                        return True
            
            # Gender (optional - only if comfortable)
            if 'gender' in question_lower:
                if self.profile.get('gender_disclosure', False):
                    gender = self.profile.get('gender', '')
                    for i, opt in enumerate(options):
                        if gender.lower() in opt:
                            select.select_by_index(i)
                            return True
                else:
                    # Select "prefer not to answer" if available
                    for i, opt in enumerate(options):
                        if 'prefer not' in opt or 'decline' in opt:
                            select.select_by_index(i)
                            return True
            
            # Race/ethnicity (optional - only if comfortable)
            if 'race' in question_lower or 'ethnicity' in question_lower:
                if self.profile.get('ethnicity_disclosure', False):
                    ethnicity = self.profile.get('ethnicity', '')
                    for i, opt in enumerate(options):
                        if ethnicity.lower() in opt:
                            select.select_by_index(i)
                            return True
                else:
                    for i, opt in enumerate(options):
                        if 'prefer not' in opt or 'decline' in opt:
                            select.select_by_index(i)
                            return True
            
            # Veteran status
            if 'veteran' in question_lower:
                is_veteran = self.profile.get('veteran', False)
                for i, opt in enumerate(options):
                    if is_veteran and 'yes' in opt:
                        select.select_by_index(i)
                        return True
                    elif not is_veteran and ('no' in opt or 'not' in opt):
                        select.select_by_index(i)
                        return True
            
            # Disability status
            if 'disability' in question_lower or 'disabled' in question_lower:
                for i, opt in enumerate(options):
                    if 'prefer not' in opt or 'decline' in opt:
                        select.select_by_index(i)
                        return True
            
            return False
            
        except Exception as e:
            logging.warning(f"Could not handle dropdown: {e}")
            return False
    
    def handle_radio_buttons(self, question_text, options):
        """Handle radio button questions"""
        question_lower = question_text.lower()
        
        # Work authorization
        if 'authorized' in question_lower or 'sponsorship' in question_lower:
            target = 'yes' if self.profile.get('work_authorized', True) else 'no'
            for option in options:
                if target in option.text.lower():
                    option.click()
                    return True
        
        # Relocation
        if 'relocate' in question_lower or 'relocation' in question_lower:
            target = 'yes' if self.profile.get('willing_to_relocate', True) else 'no'
            for option in options:
                if target in option.text.lower():
                    option.click()
                    return True
        
        # Remote work
        if 'remote' in question_lower:
            target = 'yes' if self.profile.get('open_to_remote', True) else 'no'
            for option in options:
                if target in option.text.lower():
                    option.click()
                    return True
        
        return False
    
    def handle_yes_no_question(self, question_text):
        """Determine yes/no answer based on question"""
        question_lower = question_text.lower()
        
        # Default yes questions
        yes_keywords = [
            'authorized to work',
            'eligible to work',
            'legally authorized',
            'able to work',
            'willing to relocate',
            'available to start',
            'comfortable with'
        ]
        
        # Default no questions  
        no_keywords = [
            'require sponsorship',
            'need visa',
            'criminal record',
            'been terminated'
        ]
        
        for keyword in yes_keywords:
            if keyword in question_lower:
                return True
        
        for keyword in no_keywords:
            if keyword in question_lower:
                return False
        
        # Default to True for ambiguous questions
        return True
    
    def upload_resume(self, file_input):
        """Upload resume file"""
        try:
            resume_path = self.profile.get('resume_path', '')
            if resume_path:
                file_input.send_keys(resume_path)
                time.sleep(2)
                logging.info(f"Uploaded resume: {resume_path}")
                return True
            else:
                logging.warning("No resume path configured")
                return False
        except Exception as e:
            logging.error(f"Resume upload failed: {e}")
            return False
    
    def upload_cover_letter(self, file_input):
        """Upload cover letter if available"""
        try:
            cover_letter_path = self.profile.get('cover_letter_path', '')
            if cover_letter_path:
                file_input.send_keys(cover_letter_path)
                time.sleep(2)
                logging.info(f"Uploaded cover letter: {cover_letter_path}")
                return True
            return False
        except Exception as e:
            logging.warning(f"Cover letter upload failed: {e}")
            return False
    
    def fill_linkedin_easy_apply(self, job_url):
        """
        Complete LinkedIn Easy Apply application
        Returns: (success: bool, status: str)
        """
        try:
            self.driver.get(job_url)
            time.sleep(2)
            
            # Click Easy Apply button
            easy_apply_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jobs-apply-button"))
            )
            easy_apply_btn.click()
            time.sleep(2)
            
            # Navigate through application pages
            max_pages = 10
            page_count = 0
            
            while page_count < max_pages:
                page_count += 1
                logging.info(f"Processing application page {page_count}")
                
                # Check for resume upload
                try:
                    resume_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file'][id*='resume']")
                    if resume_input and not resume_input.get_attribute('value'):
                        self.upload_resume(resume_input)
                except NoSuchElementException:
                    pass
                
                # Check for cover letter
                try:
                    cover_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file'][id*='cover']")
                    if cover_input and not cover_input.get_attribute('value'):
                        self.upload_cover_letter(cover_input)
                except NoSuchElementException:
                    pass
                
                # Fill text fields
                text_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[type='email']")
                for field in text_fields:
                    try:
                        if field.get_attribute('value'):  # Skip if already filled
                            continue
                        
                        # Get label text for context
                        label_text = ''
                        field_id = field.get_attribute('id')
                        if field_id:
                            try:
                                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                                label_text = label.text.lower()
                            except:
                                pass
                        
                        # Phone number
                        if 'phone' in label_text:
                            self.handle_phone_number(field)
                        # Years of experience
                        elif 'year' in label_text and 'experience' in label_text:
                            self.handle_years_experience(field, label_text)
                        # LinkedIn URL
                        elif 'linkedin' in label_text:
                            self.fill_text_field(field, self.profile.get('linkedin_url', ''))
                        # Website/Portfolio
                        elif 'website' in label_text or 'portfolio' in label_text:
                            self.fill_text_field(field, self.profile.get('portfolio_url', ''))
                        # GitHub
                        elif 'github' in label_text:
                            self.fill_text_field(field, self.profile.get('github_url', ''))
                    
                    except Exception as e:
                        logging.warning(f"Error filling text field: {e}")
                        continue
                
                # Fill dropdowns
                dropdowns = self.driver.find_elements(By.TAG_NAME, "select")
                for dropdown in dropdowns:
                    try:
                        # Get question text
                        dropdown_id = dropdown.get_attribute('id')
                        label_text = ''
                        if dropdown_id:
                            try:
                                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{dropdown_id}']")
                                label_text = label.text
                            except:
                                pass
                        
                        self.handle_dropdown(dropdown, label_text)
                    
                    except Exception as e:
                        logging.warning(f"Error with dropdown: {e}")
                        continue
                
                # Handle radio buttons
                radio_groups = self.driver.find_elements(By.CSS_SELECTOR, "fieldset")
                for group in radio_groups:
                    try:
                        legend = group.find_element(By.TAG_NAME, "legend")
                        question_text = legend.text
                        radio_buttons = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                        
                        self.handle_radio_buttons(question_text, radio_buttons)
                    
                    except Exception as e:
                        continue
                
                # Check for next button
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Continue'], button[aria-label*='Next']")
                    next_btn.click()
                    time.sleep(2)
                    continue
                
                except NoSuchElementException:
                    pass
                
                # Check for review button
                try:
                    review_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Review']")
                    review_btn.click()
                    time.sleep(2)
                    continue
                
                except NoSuchElementException:
                    pass
                
                # Check for submit button
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Submit'], button[aria-label*='Submit application']")
                    
                    # Check config for auto-submit
                    if self.profile.get('auto_submit', False):
                        submit_btn.click()
                        time.sleep(2)
                        logging.info("✓ Application submitted!")
                        return (True, "Applied")
                    else:
                        logging.info("⚠ Ready to submit - manual confirmation required")
                        return (True, "Ready to Submit - Confirmation Required")
                
                except NoSuchElementException:
                    pass
                
                # If we're here and no buttons found, we might be done
                break
            
            logging.warning("Reached max pages without submitting")
            return (False, "Max Pages Reached")
        
        except Exception as e:
            logging.error(f"Auto-apply error: {e}")
            return (False, f"Error: {str(e)}")
    
    def fill_greenhouse_application(self, job_url):
        """Fill Greenhouse application (many companies use this)"""
        try:
            self.driver.get(job_url)
            time.sleep(3)
            
            # Fill basic info
            fields_map = {
                'first_name': self.profile.get('first_name', ''),
                'last_name': self.profile.get('last_name', ''),
                'email': self.profile.get('email', ''),
                'phone': self.profile.get('phone', '')
            }
            
            for field_name, value in fields_map.items():
                try:
                    field = self.driver.find_element(By.ID, field_name)
                    self.fill_text_field(field, value)
                except:
                    # Try alternative selectors
                    try:
                        field = self.driver.find_element(By.NAME, field_name)
                        self.fill_text_field(field, value)
                    except:
                        continue
            
            # Upload resume
            try:
                resume_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file'][name='resume']")
                self.upload_resume(resume_input)
            except:
                pass
            
            # Submit if auto-submit enabled
            if self.profile.get('auto_submit', False):
                try:
                    submit_btn = self.driver.find_element(By.ID, "submit_app")
                    submit_btn.click()
                    time.sleep(2)
                    return (True, "Applied")
                except:
                    pass
            
            return (True, "Ready to Submit - Manual Review Required")
        
        except Exception as e:
            logging.error(f"Greenhouse application error: {e}")
            return (False, f"Error: {str(e)}")
    
    def fill_workday_application(self, job_url):
        """Fill Workday application (common for large companies)"""
        # Workday is notoriously difficult to automate
        # This is a basic implementation
        try:
            self.driver.get(job_url)
            time.sleep(3)
            
            # Click Apply button
            apply_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-automation-id='apply']"))
            )
            apply_btn.click()
            time.sleep(2)
            
            # Workday usually requires manual sign-in or resume upload
            logging.info("Workday detected - manual interaction likely required")
            return (False, "Manual Application Required - Workday")
        
        except Exception as e:
            logging.error(f"Workday application error: {e}")
            return (False, f"Error: {str(e)}")

def load_profile(profile_file='profile.json'):
    """Load your profile data"""
    with open(profile_file, 'r') as f:
        return json.load(f)
