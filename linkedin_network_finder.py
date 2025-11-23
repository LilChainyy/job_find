"""
LinkedIn Network Finder
After applying to a job, finds 2 relevant people at the company to network with
Looks for people 1 level above your target role
"""

import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
import logging
import pandas as pd
from datetime import datetime

class LinkedInNetworkFinder:
    def __init__(self, driver, profile_data):
        """
        Initialize with driver and profile
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.profile = profile_data
        
        # Define target titles based on your career level
        # If you're applying for "Analyst" roles, look for "Senior Analyst", "Manager", etc.
        self.target_seniority_map = {
            'analyst': ['senior analyst', 'lead analyst', 'manager', 'associate'],
            'associate': ['senior associate', 'vice president', 'manager', 'director'],
            'senior': ['director', 'vice president', 'head of'],
            'manager': ['senior manager', 'director', 'vice president']
        }
    
    def determine_target_titles(self, job_title):
        """
        Based on the job you applied to, determine what titles to search for networking
        """
        job_title_lower = job_title.lower()
        
        # Determine your level from job title
        if 'senior' in job_title_lower and 'analyst' in job_title_lower:
            return ['manager', 'senior manager', 'director']
        elif 'analyst' in job_title_lower:
            return ['senior analyst', 'lead analyst', 'manager', 'associate manager']
        elif 'associate' in job_title_lower:
            return ['senior associate', 'assistant vice president', 'vice president', 'manager']
        elif 'specialist' in job_title_lower:
            return ['senior specialist', 'manager', 'team lead']
        else:
            # Default: look for managers and directors
            return ['manager', 'senior manager', 'director']
    
    def find_people_at_company(self, company_name, job_title, department_hint=None, max_results=5):
        """
        Find relevant people at the company to network with
        
        Args:
            company_name: Name of the company
            job_title: The job title you applied for
            department_hint: Optional hint like "operations", "trading", etc.
            max_results: Max number of people to find
            
        Returns:
            List of dicts with person info
        """
        try:
            logging.info(f"Finding people at {company_name} for networking...")
            
            # Determine target titles
            target_titles = self.determine_target_titles(job_title)
            
            # Build LinkedIn search query
            # Search for people at company with target titles
            search_queries = []
            
            if department_hint:
                # Search with department
                for title in target_titles[:2]:  # Limit to top 2 titles
                    query = f"{title} {department_hint} at {company_name}"
                    search_queries.append(query)
            else:
                # Search without department
                for title in target_titles[:2]:
                    query = f"{title} at {company_name}"
                    search_queries.append(query)
            
            people_found = []
            
            for query in search_queries:
                if len(people_found) >= max_results:
                    break
                
                # Navigate to LinkedIn people search
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}"
                self.driver.get(search_url)
                time.sleep(3)
                
                # Get search results
                try:
                    result_cards = self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "li.reusable-search__result-container"
                    )
                    
                    for card in result_cards[:3]:  # Top 3 from each search
                        if len(people_found) >= max_results:
                            break
                        
                        try:
                            person_data = self.extract_person_data(card, company_name)
                            
                            if person_data and self.is_good_connection(person_data, job_title):
                                people_found.append(person_data)
                                logging.info(f"Found: {person_data['name']} - {person_data['title']}")
                        
                        except Exception as e:
                            logging.warning(f"Error extracting person data: {e}")
                            continue
                
                except Exception as e:
                    logging.warning(f"Error in search results: {e}")
                    continue
                
                time.sleep(2)  # Rate limiting
            
            # Rank and return top results
            ranked_people = self.rank_connections(people_found, job_title)
            return ranked_people[:2]  # Return top 2
        
        except Exception as e:
            logging.error(f"Error finding people: {e}")
            return []
    
    def extract_person_data(self, result_card, company_name):
        """Extract data from a LinkedIn search result card"""
        try:
            # Get name and profile URL
            name_elem = result_card.find_element(By.CSS_SELECTOR, "span.entity-result__title-text a")
            name = name_elem.text.strip()
            profile_url = name_elem.get_attribute('href').split('?')[0]  # Remove query params
            
            # Get title
            title_elem = result_card.find_element(By.CSS_SELECTOR, "div.entity-result__primary-subtitle")
            title = title_elem.text.strip()
            
            # Get location if available
            try:
                location_elem = result_card.find_element(By.CSS_SELECTOR, "div.entity-result__secondary-subtitle")
                location = location_elem.text.strip()
            except:
                location = "Unknown"
            
            # Check if you have mutual connections
            mutual_connections = 0
            try:
                mutual_elem = result_card.find_element(By.CSS_SELECTOR, "span.entity-result__simple-insight-text")
                mutual_text = mutual_elem.text
                if 'mutual connection' in mutual_text.lower():
                    # Extract number
                    import re
                    match = re.search(r'(\d+)', mutual_text)
                    if match:
                        mutual_connections = int(match.group(1))
            except:
                pass
            
            # Check if already connected
            is_connected = False
            try:
                connected_elem = result_card.find_element(By.CSS_SELECTOR, "span.entity-result__badge-text")
                if '1st' in connected_elem.text or 'connected' in connected_elem.text.lower():
                    is_connected = True
            except:
                pass
            
            return {
                'name': name,
                'title': title,
                'company': company_name,
                'location': location,
                'profile_url': profile_url,
                'mutual_connections': mutual_connections,
                'is_connected': is_connected,
                'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        except Exception as e:
            logging.warning(f"Could not extract person data: {e}")
            return None
    
    def is_good_connection(self, person_data, job_title):
        """
        Determine if this person is a good networking target
        """
        title = person_data['title'].lower()
        
        # Skip if already connected
        if person_data['is_connected']:
            return False
        
        # Skip recruiters (you want actual team members)
        if 'recruiter' in title or 'talent acquisition' in title:
            return False
        
        # Skip very senior people (CEO, CFO) unless specifically relevant
        if any(word in title for word in ['ceo', 'cfo', 'chief', 'founder', 'president']) and \
           not any(word in title for word in ['vp', 'vice president']):
            return False
        
        # Prefer people in relevant departments
        job_lower = job_title.lower()
        relevant_keywords = []
        
        if 'operations' in job_lower or 'trade' in job_lower:
            relevant_keywords = ['operations', 'trade', 'trading', 'settlement', 'middle office']
        elif 'quant' in job_lower:
            relevant_keywords = ['quant', 'research', 'trading', 'strategy']
        elif 'analyst' in job_lower:
            relevant_keywords = ['analyst', 'analysis', 'research']
        
        # Boost score if title contains relevant keywords
        has_relevant_keywords = any(keyword in title for keyword in relevant_keywords)
        
        return has_relevant_keywords or person_data['mutual_connections'] > 0
    
    def rank_connections(self, people, job_title):
        """
        Rank people by how good of a connection they'd be
        """
        for person in people:
            score = 0
            title = person['title'].lower()
            
            # Higher score for mutual connections
            score += person['mutual_connections'] * 10
            
            # Higher score for relevant titles
            job_lower = job_title.lower()
            if 'operations' in job_lower:
                if 'operations' in title:
                    score += 20
                if 'trade' in title or 'trading' in title:
                    score += 15
                if 'manager' in title:
                    score += 10
            
            if 'analyst' in job_lower:
                if 'senior' in title or 'lead' in title:
                    score += 15
                if 'manager' in title:
                    score += 20
            
            # Prefer people at right seniority level (not too junior, not too senior)
            if any(word in title for word in ['manager', 'senior', 'lead', 'director']):
                score += 15
            if any(word in title for word in ['vp', 'vice president', 'head of']):
                score += 10
            
            person['networking_score'] = score
        
        # Sort by score
        people.sort(key=lambda x: x['networking_score'], reverse=True)
        return people
    
    def generate_connection_message(self, person_data, job_data):
        """
        Generate a personalized LinkedIn connection request message
        """
        templates = [
            # Template 1: Mutual interest
            f"Hi {person_data['name'].split()[0]}, I recently applied for the {job_data['title']} position at {person_data['company']} and was impressed by the team's work in {self.extract_department(person_data['title'])}. I'd love to connect and learn more about your experience there.",
            
            # Template 2: Background alignment
            f"Hi {person_data['name'].split()[0]}, I'm exploring opportunities in {self.extract_department(person_data['title'])} and saw your background at {person_data['company']}. I recently applied for a role there and would value the chance to connect.",
            
            # Template 3: Career transition
            f"Hi {person_data['name'].split()[0]}, I'm transitioning into {self.extract_department(job_data['title'])} and recently applied to {person_data['company']}. Your experience as a {person_data['title']} would be valuable to learn from. Would you be open to connecting?"
        ]
        
        # Choose template based on mutual connections
        if person_data['mutual_connections'] > 0:
            message = f"Hi {person_data['name'].split()[0]}, I noticed we have {person_data['mutual_connections']} mutual connection{'s' if person_data['mutual_connections'] > 1 else ''}. I recently applied for the {job_data['title']} role at {person_data['company']} and would love to connect and learn about your experience there."
        else:
            message = templates[0]  # Use first template
        
        # Ensure message is under LinkedIn's 300 character limit
        if len(message) > 295:
            message = message[:292] + "..."
        
        return message
    
    def extract_department(self, title):
        """Extract department/function from title"""
        title_lower = title.lower()
        
        departments = {
            'operations': ['operations', 'ops'],
            'trading': ['trading', 'trade', 'trader'],
            'risk': ['risk'],
            'technology': ['technology', 'engineering', 'developer'],
            'quantitative': ['quant', 'quantitative'],
            'research': ['research']
        }
        
        for dept, keywords in departments.items():
            if any(kw in title_lower for kw in keywords):
                return dept
        
        return 'this field'
    
    def save_networking_targets(self, people, job_data, filename='networking_targets.csv'):
        """Save networking targets to CSV"""
        try:
            # Add job context to each person
            for person in people:
                person['job_applied'] = job_data.get('title', '')
                person['job_url'] = job_data.get('url', '')
                person['connection_message'] = self.generate_connection_message(person, job_data)
            
            # Load existing file or create new
            try:
                existing_df = pd.read_csv(filename)
                df = pd.DataFrame(people)
                combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['profile_url'], keep='last')
            except FileNotFoundError:
                combined_df = pd.DataFrame(people)
            
            combined_df.to_csv(filename, index=False)
            logging.info(f"Saved {len(people)} networking targets to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving networking targets: {e}")
    
    def find_and_save_networking_contacts(self, job_data):
        """
        Main function: After applying to a job, find relevant people and save them
        
        Args:
            job_data: Dict with job info (title, company, url, etc.)
        
        Returns:
            List of people found
        """
        company_name = job_data.get('company', '')
        job_title = job_data.get('title', '')
        
        # Extract department hint from job title
        department_hint = None
        job_lower = job_title.lower()
        if 'operations' in job_lower or 'trade' in job_lower:
            department_hint = 'operations'
        elif 'quant' in job_lower:
            department_hint = 'quantitative'
        elif 'risk' in job_lower:
            department_hint = 'risk'
        
        # Find people
        people = self.find_people_at_company(
            company_name=company_name,
            job_title=job_title,
            department_hint=department_hint,
            max_results=5  # Find 5, return top 2
        )
        
        if people:
            # Save to CSV
            self.save_networking_targets(people, job_data)
            
            # Print summary
            logging.info(f"\n{'='*60}")
            logging.info(f"NETWORKING TARGETS FOUND FOR {company_name}")
            logging.info(f"{'='*60}")
            
            for i, person in enumerate(people[:2], 1):
                logging.info(f"\n{i}. {person['name']}")
                logging.info(f"   Title: {person['title']}")
                logging.info(f"   Location: {person['location']}")
                logging.info(f"   Mutual Connections: {person['mutual_connections']}")
                logging.info(f"   Profile: {person['profile_url']}")
                logging.info(f"   Suggested Message:")
                logging.info(f"   \"{person['connection_message']}\"")
            
            logging.info(f"\n{'='*60}\n")
        else:
            logging.warning(f"No networking targets found for {company_name}")
        
        return people[:2]  # Return top 2

def integrate_with_job_monitor(job_monitor_instance, job_data):
    """
    Integration function to use after applying to a job
    Call this in your job_monitor.py after a successful application
    """
    try:
        # Load profile
        with open('profile.json', 'r') as f:
            profile = json.load(f)
        
        # Create network finder
        network_finder = LinkedInNetworkFinder(
            driver=job_monitor_instance.driver,
            profile_data=profile
        )
        
        # Find people
        people = network_finder.find_and_save_networking_contacts(job_data)
        
        return people
    
    except Exception as e:
        logging.error(f"Error in networking integration: {e}")
        return []
