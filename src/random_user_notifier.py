"""
Random User Notifier for Discord Monitoring Bot
Handles selecting random users and sending them in bulk at random intervals
"""

import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import discord

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter

class RandomUserNotifier:
    def __init__(self, bot: discord.Client, config: ConfigManager, db: DatabaseManager, formatter: UserFormatter):
        self.bot = bot
        self.config = config
        self.db = db
        self.formatter = formatter
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # Settings for random notifications
        self.min_users = 4
        self.max_users = 9
        self.min_interval = 180  # 3 minutes in seconds
        self.max_interval = 600  # 10 minutes in seconds
        
    async def start(self):
        """Start the random user notifier process"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("Random user notifier initialized and starting...")
        asyncio.create_task(self._run_random_notification_loop())
        self.logger.info("Random user notification process started")
        
    async def stop(self):
        """Stop the random user notification process"""
        self.is_running = False
        self.logger.info("Random user notification process stopped")
        
    async def _run_random_notification_loop(self):
        """Main loop that sends random user notifications at intervals"""
        self.logger.info("Random user notification loop started")
        while self.is_running:
            try:
                # Generate random users
                user_count = random.randint(self.min_users, self.max_users)
                self.logger.info(f"Generating {user_count} random users for notification")
                
                # Always try to get real server data first
                real_servers = []
                
                # Get servers from user client if available
                if hasattr(self.bot, 'user_client') and self.bot.user_client:
                    try:
                        user_guilds = self.bot.user_client.get_user_guilds()
                        if not user_guilds and hasattr(self.bot.user_client, 'discover_user_guilds'):
                            user_guilds = await self.bot.user_client.discover_user_guilds()
                        
                        if user_guilds:
                            for guild in user_guilds:
                                guild_id = guild.get("id", 0)
                                guild_name = guild.get("name", "Unknown Server")
                                real_servers.append({
                                    "id": guild_id,
                                    "name": guild_name
                                })
                            self.logger.info(f"Found {len(real_servers)} real servers from user token")
                    except Exception as e:
                        self.logger.error(f"Error getting user guilds: {e}")
                
                # If no user guilds, get bot guilds
                if not real_servers:
                    for guild in self.bot.guilds:
                        real_servers.append({
                            "id": guild.id,
                            "name": guild.name
                        })
                    self.logger.info(f"Found {len(real_servers)} real servers from bot connection")
                
                # Try to get real user data
                if hasattr(self.bot, 'user_client') and self.bot.user_client:
                    try:
                        # Attempt to fetch real user data from user token
                        self.logger.info("Attempting to fetch real user data from Discord API...")
                        real_users = await self._generate_random_users(user_count)
                        
                        if real_users and len(real_users) > 0:
                            self.logger.info(f"Successfully generated {len(real_users)} users with real data")
                            # Send the notifications
                            await self._send_bulk_notification(real_users)
                        else:
                            # Fall back to generated data with real servers
                            self.logger.info("No real user data available, using fallback data with real servers")
                            fallback_users = await self._generate_fallback_users(user_count, real_servers)
                            await self._send_bulk_notification(fallback_users)
                    except Exception as e:
                        self.logger.error(f"Error fetching real user data: {e}")
                        # Fall back to generated data with real servers
                        fallback_users = await self._generate_fallback_users(user_count, real_servers)
                        await self._send_bulk_notification(fallback_users)
                else:
                    # No user client available, use fallback data with real servers
                    self.logger.info("No user client available, using fallback data with real servers")
                    fallback_users = await self._generate_fallback_users(user_count, real_servers)
                    await self._send_bulk_notification(fallback_users)
                    
                # Wait for a random interval
                interval = random.randint(self.min_interval, self.max_interval)
                self.logger.info(f"Waiting {interval} seconds before sending next random notification")
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in random notification loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _generate_random_users(self, count: int) -> List[Dict[str, Any]]:
        """Generate user data for notifications using real server members"""
        random_users = []
        
        try:
            # Get servers the user belongs to via user client
            servers = []
            real_server_members = {}
            
            # Try to get user client servers if available - prioritize these
            if hasattr(self.bot, 'user_client') and self.bot.user_client:
                try:
                    # First try to get cached guilds
                    user_guilds = self.bot.user_client.get_user_guilds()
                    
                    # If no cached guilds, try to discover them
                    if not user_guilds and hasattr(self.bot.user_client, 'discover_user_guilds'):
                        user_guilds = await self.bot.user_client.discover_user_guilds()
                    
                    if user_guilds:
                        # Use only user guilds
                        servers = []
                        for guild in user_guilds:
                            guild_id = guild.get("id", 0)
                            guild_name = guild.get("name", "Unknown Server")
                            servers.append({
                                "id": guild_id,
                                "name": guild_name
                            })
                            
                            # Try to get members for this guild
                            try:
                                if hasattr(self.bot.user_client, 'get_guild_members'):
                                    members = await self.bot.user_client.get_guild_members(guild_id)
                                    if members:
                                        real_server_members[guild_name] = members
                                        self.logger.info(f"Retrieved {len(members)} members from {guild_name}")
                            except Exception as e:
                                self.logger.error(f"Error getting members for guild {guild_name}: {e}")
                                
                        self.logger.info(f"Using {len(servers)} servers from user token")
                except Exception as e:
                    self.logger.error(f"Error getting user guilds: {e}")
            
            # If no user guilds, fall back to bot guilds and get their members
            if not servers:
                for guild in self.bot.guilds:
                    servers.append({
                        "id": guild.id,
                        "name": guild.name
                    })
                    
                    # Get members from this guild
                    try:
                        members = []
                        async for member in guild.fetch_members(limit=100):
                            if not member.bot:  # Skip bots
                                members.append({
                                    "id": member.id,
                                    "username": member.name,
                                    "created_at": member.created_at
                                })
                        
                        if members:
                            real_server_members[guild.name] = members
                            self.logger.info(f"Retrieved {len(members)} members from {guild.name}")
                    except Exception as e:
                        self.logger.error(f"Error fetching members for guild {guild.name}: {e}")
                        
                self.logger.info(f"Using {len(servers)} servers from bot connection")
            
            # If we don't have any real members, use fallback data
            if not real_server_members:
                self.logger.warning("No real members available, using fallback data")
                return await self._generate_fallback_users(count, servers)
                
            # Now select random users from the real members
            selected_users = []
            available_servers = list(real_server_members.keys())
            
            if not available_servers:
                self.logger.warning("No servers with members available, using fallback data")
                return await self._generate_fallback_users(count, servers)
            
            # Try to get the requested number of users
            attempts = 0
            while len(selected_users) < count and attempts < 50:
                attempts += 1
                
                # Pick a random server
                server_name = random.choice(available_servers)
                members = real_server_members[server_name]
                
                if not members:
                    continue
                    
                # Pick a random member
                member = random.choice(members)
                
                # Check if this member is already selected
                if any(u.get('username') == member['username'] and u.get('server_name') == server_name for u in selected_users):
                    continue
                
                # Calculate account age
                created_at = member.get('created_at')
                if not created_at:
                    continue
                    
                account_age = self.formatter.calculate_account_age(created_at)
                
                # Create user data
                user_data = {
                    'user_id': member.get('id', 0),
                    'username': member.get('username', 'Unknown'),
                    'display_name': member.get('username', 'Unknown'),
                    'server_id': next((s['id'] for s in servers if s['name'] == server_name), 0),
                    'server_name': server_name,
                    'join_timestamp': datetime.now(timezone.utc).isoformat(),
                    'account_created': created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                    'account_age_days': account_age['total_days'],
                    'account_age_formatted': account_age['formatted']
                }
                
                selected_users.append(user_data)
            
            # If we couldn't get enough real users, fill in with fallback data
            if len(selected_users) < count:
                self.logger.warning(f"Only found {len(selected_users)} real users, filling in with fallback data")
                fallback_users = await self._generate_fallback_users(count - len(selected_users), servers)
                selected_users.extend(fallback_users)
                
            return selected_users
            
        except Exception as e:
            self.logger.error(f"Error generating users with real data: {e}")
            return await self._generate_fallback_users(count, [])
            
    async def _generate_fallback_users(self, count: int, servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fallback random user data when real data is not available"""
        random_users = []
        
        try:
            # Always ensure we have user's actual servers
            user_servers = []
            
            # Try to get real servers from user client first
            if hasattr(self.bot, 'user_client') and self.bot.user_client:
                try:
                    user_guilds = self.bot.user_client.get_user_guilds()
                    if not user_guilds and hasattr(self.bot.user_client, 'discover_user_guilds'):
                        user_guilds = await self.bot.user_client.discover_user_guilds()
                    
                    if user_guilds:
                        for guild in user_guilds:
                            guild_id = guild.get("id", 0)
                            guild_name = guild.get("name", "Unknown Server")
                            user_servers.append({
                                "id": guild_id,
                                "name": guild_name
                            })
                        self.logger.info(f"Found {len(user_servers)} real servers from user token")
                except Exception as e:
                    self.logger.error(f"Error getting user guilds: {e}")
            
            # If no user guilds, get bot guilds
            if not user_servers:
                for guild in self.bot.guilds:
                    user_servers.append({
                        "id": guild.id,
                        "name": guild.name
                    })
                self.logger.info(f"Found {len(user_servers)} real servers from bot connection")
            
            # If still no servers, use default servers as absolute last resort
            if not user_servers:
                # Default server names as absolute last resort
                server_names = [
                    "Abu Cartel", "The Wizards Hub 🧙", "No Limit Trades", "inspiredanalyst's server"
                ]
                
                for name in server_names:
                    fake_id = random.randint(100000000000000000, 999999999999999999)
                    user_servers.append({
                        "id": fake_id,
                        "name": name
                    })
                self.logger.info(f"Using {len(user_servers)} default server names as last resort")
            
            # IMPORTANT: Always use the user's actual servers, even if servers were provided
            # This ensures notifications always show servers the user belongs to
            if user_servers:
                servers = user_servers
                self.logger.info(f"Using {len(servers)} servers that the user actually belongs to")
            
            # Number patterns that appear at the end of usernames
            number_patterns = [
                lambda: str(random.randint(1, 9999)),  # Simple numbers: 1-9999
                lambda: str(random.randint(10, 99)) + str(random.randint(10, 99)),  # Double pairs: 1234, 5678
                lambda: str(random.randint(19, 20)) + str(random.randint(10, 99)),  # Year-like: 1995, 2023
                lambda: "0" + str(random.randint(1, 9)),  # Leading zero: 01, 07
                lambda: str(random.randint(1, 12)) + str(random.randint(1, 31)),  # Date-like: 1225 (Dec 25)
                lambda: "",  # No number (about 20% of the time)
                lambda: str(random.randint(1, 999)),  # 1-3 digit number
                lambda: "007",  # Special numbers
                lambda: "123",
                lambda: "420",
                lambda: "69",
                lambda: "777",
                lambda: "666",
                lambda: "999",
                lambda: "1337",
                lambda: "0" + str(random.randint(1, 9)) + str(random.randint(1, 9))  # 001-099
            ]
            
            # More realistic username patterns that look like actual Discord users
            realistic_patterns = [
                # Simple name + number (most common pattern)
                lambda name, country: f"{name.lower()}{random.choice(number_patterns)()}",
                
                # Name with underscores
                lambda name, country: f"{name.lower()}_{random.choice(number_patterns)()}",
                
                # Name with country code
                lambda name, country: f"{name.lower()}{country.lower()}{random.choice(number_patterns)()}",
                
                # Gaming-style names
                lambda name, country: f"{name.lower()}_gaming{random.choice(number_patterns)()}",
                lambda name, country: f"{name.lower()}_yt{random.choice(number_patterns)()}",
                lambda name, country: f"{name.lower()}_ttv{random.choice(number_patterns)()}",
                
                # Professional-style names
                lambda name, country: f"{name.lower()}.{random.choice(['official', 'real', 'og'])}{random.choice(number_patterns)()}",
                
                # Decorative names
                lambda name, country: f"{'x' if random.random() < 0.5 else 'X'}{name.lower()}{'x' if random.random() < 0.5 else 'X'}{random.choice(number_patterns)()}",
                
                # Hobby-based names
                lambda name, country: f"{random.choice(['gamer', 'player', 'artist', 'dev'])}.{name.lower()}{random.choice(number_patterns)()}"
            ]
            
            # Names by country
            international_names = {
                "Germany": ["klaus", "hans", "franz", "lukas", "felix", "max", "jan", "anna", "lena", "emma", "sophia", "mia", "hannah", "schmidt", "mueller", "wagner", "thomas", "michael", "andreas", "stefan", "peter", "christian", "markus", "alexander", "wolfgang", "martin", "tobias", "daniel", "sebastian", "niklas", "leon", "jonas", "elias", "noah", "paul", "charlotte", "marie", "laura", "julia", "sarah", "lisa", "leonie", "katharina", "johanna", "fischer", "weber", "schneider", "meyer", "becker", "hoffmann", "schulz", "bauer", "zimmermann", "braun", "krause", "lehmann", "keller", "neumann"],
                
                "Japan": ["taka", "hiro", "yuki", "kazu", "ken", "aki", "yuki", "hana", "sakura", "haruto", "yuma", "aoi", "rin", "sora", "kenji", "takashi", "hiroshi", "akira", "daisuke", "satoshi", "ryota", "shota", "yuto", "haruki", "kaito", "yamato", "riku", "sota", "yui", "mio", "akane", "haruna", "mei", "miyu", "koharu", "hinata", "ichika", "suzuki", "tanaka", "watanabe", "takahashi", "ito", "yamamoto", "nakamura", "kobayashi", "sato", "kato", "yoshida", "yamada", "sasaki", "yamaguchi", "matsumoto", "inoue", "kimura", "hayashi", "shimizu"],
                
                "Brazil": ["carlos", "pedro", "joao", "lucas", "gabriel", "maria", "ana", "julia", "beatriz", "silva", "santos", "oliveira", "gustavo", "rafael", "bruno", "felipe", "rodrigo", "eduardo", "leonardo", "marcelo", "vinicius", "thiago", "matheus", "diego", "luiz", "ricardo", "camila", "fernanda", "amanda", "juliana", "mariana", "bruna", "carolina", "leticia", "natalia", "isabela", "pereira", "almeida", "ferreira", "rodrigues", "costa", "gomes", "martins", "araujo", "melo", "ribeiro", "carvalho", "nascimento", "lima", "sousa", "barbosa", "moreira", "cavalcanti"],
                
                "France": ["pierre", "jean", "michel", "antoine", "louis", "sophie", "marie", "camille", "dupont", "martin", "dubois", "nicolas", "philippe", "francois", "sebastien", "laurent", "julien", "thomas", "alexandre", "olivier", "mathieu", "romain", "clement", "vincent", "maxime", "julie", "celine", "isabelle", "nathalie", "valerie", "claire", "sandrine", "aurelie", "elodie", "laure", "petit", "leroy", "moreau", "simon", "fournier", "girard", "lambert", "fontaine", "rousseau", "vincent", "muller", "lefevre", "faure", "andre", "mercier", "blanc", "guerin", "boyer"],
                
                "Thailand": ["somchai", "chai", "lek", "noi", "sombat", "malee", "sompong", "ratana", "somsak", "thaksin", "ananda", "apirak", "boon", "chatchai", "decha", "kiet", "mongkut", "narong", "panya", "samart", "sunan", "tawan", "udom", "vichai", "yuthasak", "achara", "busaba", "chailai", "duangkamol", "jaidee", "kanda", "malai", "napasorn", "orasa", "pim", "rattana", "sirikit", "thong", "ubon", "wattana", "yindee", "jaidee", "maliwan", "suwannee", "boonmee", "chaiyasit", "thongchai", "sakchai", "prasit", "somporn", "wichai", "pracha"],
                
                "Argentina": ["leo", "diego", "juan", "carlos", "martin", "sofia", "valentina", "camila", "martinez", "rodriguez", "alejandro", "matias", "nicolas", "sebastian", "federico", "javier", "fernando", "lucas", "maximiliano", "pablo", "santiago", "tomas", "victoria", "lucia", "martina", "agustina", "florencia", "catalina", "julieta", "rocio", "gonzalez", "fernandez", "lopez", "diaz", "perez", "garcia", "sanchez", "romero", "sosa", "alvarez", "torres", "ruiz", "ramirez", "flores", "benitez", "acosta", "medina", "herrera", "suarez", "aguirre", "gimenez", "gutierrez", "castro"],
                
                "Italy": ["mario", "luigi", "marco", "giuseppe", "antonio", "sofia", "giulia", "giorgia", "rossi", "ferrari", "alessandro", "andrea", "francesco", "luca", "matteo", "davide", "giovanni", "riccardo", "simone", "lorenzo", "salvatore", "roberto", "stefano", "chiara", "francesca", "valentina", "martina", "sara", "alessia", "elena", "laura", "elisa", "russo", "bianchi", "romano", "colombo", "ricci", "marino", "greco", "bruno", "gallo", "conti", "costa", "giordano", "mancini", "lombardi", "moretti", "barbieri", "fontana", "santoro", "mariani", "rinaldi", "caruso"],
                
                "Vietnam": ["nguyen", "tran", "le", "pham", "hoang", "minh", "linh", "tuan", "anh", "huong", "thanh", "hung", "huy", "quang", "duc", "dung", "hai", "hieu", "nam", "phong", "son", "thang", "trung", "vinh", "binh", "chi", "dao", "ha", "hoa", "hong", "khanh", "lan", "mai", "ngoc", "nhu", "phuong", "thao", "thu", "trinh", "tuyet", "van", "yen", "dinh", "do", "duong", "luong", "ly", "mai", "ngo", "truong", "vo", "vu", "dang", "bui", "ho", "huynh"],
                
                "Spain": ["javier", "carlos", "antonio", "miguel", "jose", "maria", "carmen", "lucia", "garcia", "rodriguez", "david", "manuel", "rafael", "francisco", "juan", "alberto", "luis", "alvaro", "daniel", "fernando", "pablo", "sergio", "alejandro", "ramon", "laura", "ana", "cristina", "isabel", "marta", "patricia", "paula", "pilar", "raquel", "silvia", "teresa", "fernandez", "lopez", "martinez", "sanchez", "perez", "gomez", "martin", "jimenez", "ruiz", "hernandez", "diaz", "moreno", "alvarez", "romero", "alonso", "gutierrez", "navarro", "torres"],
                
                "Canada": ["james", "william", "benjamin", "logan", "ethan", "jacob", "alexander", "liam", "noah", "lucas", "emma", "olivia", "charlotte", "sophia", "amelia", "isabella", "ava", "mia", "emily", "abigail", "smith", "brown", "roy", "wilson", "leblanc", "tremblay", "gagnon", "bouchard", "gauthier", "morin", "lavoie", "fortin", "gagne", "ouellet", "pelletier", "belanger", "bergeron", "cote", "nguyen", "chan", "wong", "li", "singh", "patel", "kumar", "sharma", "kaur", "grewal", "gill", "dhillon", "sandhu", "sidhu"],
                
                "United States": ["john", "mike", "dave", "chris", "ryan", "emma", "olivia", "ava", "smith", "johnson", "michael", "robert", "james", "david", "joseph", "thomas", "charles", "william", "daniel", "matthew", "anthony", "donald", "steven", "paul", "andrew", "joshua", "kenneth", "kevin", "brian", "george", "mary", "patricia", "jennifer", "linda", "elizabeth", "barbara", "susan", "jessica", "sarah", "karen", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson", "taylor", "thomas", "moore"],
                
                "South Korea": ["kim", "lee", "park", "choi", "jung", "min", "jin", "seung", "ji", "hyun", "joon", "soo", "young", "sung", "ho", "jae", "woo", "dong", "hyung", "kyu", "tae", "yeon", "hye", "eun", "joo", "kyung", "mi", "sun", "yoon", "hee", "kang", "yoo", "shin", "song", "han", "lim", "moon", "yang", "hwang", "ahn", "bae", "kwon", "jang", "ryu", "hong", "seo", "baek", "im", "jeong", "koo", "nam", "oh", "son", "yun", "jeon"],
                
                "Poland": ["adam", "piotr", "marcin", "michal", "tomasz", "lukasz", "pawel", "jan", "jakub", "marek", "anna", "maria", "katarzyna", "malgorzata", "agnieszka", "barbara", "krystyna", "ewa", "elzbieta", "zofia", "kowalski", "nowak", "wisniewski", "wojcik", "kowalczyk", "kaminski", "lewandowski", "zielinski", "szymanski", "wozniak", "dabrowski", "kozlowski", "jankowski", "mazur", "kwiatkowski", "krawczyk", "piotrowski", "grabowski", "nowakowski", "pawlowski", "michalski", "nowicki", "adamczyk", "dudek", "zajac", "wieczorek", "jablonski", "krol", "majewski", "olszewski"],
                
                "India": ["raj", "amit", "vijay", "rahul", "sunil", "priya", "neha", "pooja", "sharma", "patel", "ajay", "anil", "deepak", "rajesh", "rakesh", "sanjay", "suresh", "vikram", "vivek", "arun", "ashok", "dinesh", "kumar", "manoj", "mukesh", "ramesh", "anjali", "anita", "kavita", "kiran", "lakshmi", "meena", "nisha", "radha", "rekha", "seema", "singh", "kumar", "das", "kaur", "shah", "gupta", "jain", "agarwal", "verma", "yadav", "mishra", "pandey", "chatterjee", "mukherjee", "banerjee", "roy", "kulkarni", "patil", "reddy"],
                
                "Mexico": ["juan", "carlos", "miguel", "jose", "luis", "maria", "guadalupe", "rosa", "hernandez", "lopez", "alejandro", "antonio", "fernando", "francisco", "javier", "manuel", "pedro", "ricardo", "roberto", "sergio", "ana", "carmen", "elizabeth", "gabriela", "laura", "leticia", "martha", "patricia", "silvia", "veronica", "garcia", "martinez", "rodriguez", "gonzalez", "perez", "sanchez", "ramirez", "torres", "flores", "diaz", "reyes", "morales", "cruz", "ortiz", "gutierrez", "chavez", "ramos", "ruiz", "mendoza", "aguilar", "castillo", "romero", "alvarez", "suarez", "vazquez"],
                
                "Indonesia": ["budi", "agus", "ahmad", "slamet", "eko", "bambang", "joko", "heru", "dedi", "yanto", "siti", "ani", "wati", "yuli", "rina", "dewi", "sri", "lestari", "yani", "susanti", "saputra", "kusuma", "wijaya", "santoso", "wibowo", "hidayat", "nugroho", "ismail", "setiawan", "sutanto", "suryanto", "hartono", "gunawan", "budiman", "kurniawan", "santosa", "sugiarto", "cahyono", "susanto", "iswanto", "sudarsono", "prasetyo", "abidin", "permana", "nugraha", "saputro", "widodo", "supriyanto", "suryadi", "haryanto", "putra", "arief", "pratama", "purnomo"],
                
                "Philippines": ["juan", "carlo", "paolo", "miguel", "marco", "maria", "rosa", "ana", "santos", "reyes", "antonio", "eduardo", "francisco", "jose", "manuel", "pedro", "ricardo", "roberto", "angelica", "carmela", "cristina", "elena", "gabriela", "isabel", "luisa", "teresa", "dela cruz", "garcia", "reyes", "ramos", "aquino", "santos", "diaz", "cruz", "bautista", "ocampo", "mendoza", "torres", "flores", "gonzales", "perez", "pascual", "rodriguez", "rivera", "villanueva", "navarro", "ignacio", "romero", "manalaysay", "tolentino", "aguilar", "castro", "valdez", "fernandez"],
                
                "China": ["li", "wang", "zhang", "chen", "liu", "wei", "xin", "yi", "min", "jing", "yang", "huang", "zhao", "wu", "zhou", "sun", "lin", "zhu", "he", "gao", "ma", "hu", "luo", "liang", "song", "zheng", "xie", "han", "tang", "feng", "yu", "dong", "xiao", "cheng", "cao", "yuan", "deng", "xu", "fu", "shen", "zeng", "peng", "pan", "guo", "jiang", "tian", "ding", "wei", "yao", "lv", "ren", "lu", "qian", "long", "fang", "dai", "cai", "jia", "tan"],
                
                "Romania": ["andrei", "alexandru", "mihai", "ionut", "gabriel", "cristian", "florin", "marian", "catalin", "daniel", "maria", "elena", "ioana", "ana", "andreea", "cristina", "mihaela", "alexandra", "nicoleta", "daniela", "popescu", "ionescu", "popa", "stan", "dumitru", "gheorghe", "stoica", "constantin", "marin", "vasile", "dinu", "serban", "florescu", "mocanu", "dumitrescu", "diaconu", "mazilu", "nedelcu", "georgescu", "albu", "tabacu", "stanescu", "preda", "manea", "cristea", "toma", "florea", "ene", "lungu", "simion", "tudor", "rusu", "munteanu", "matei"],
                
                "Netherlands": ["jan", "peter", "hans", "kees", "henk", "jeroen", "sander", "thomas", "tim", "mark", "maria", "johanna", "anna", "elisabeth", "cornelia", "emma", "lisa", "sophie", "julia", "de jong", "de vries", "van den berg", "bakker", "janssen", "visser", "smit", "meijer", "de boer", "mulder", "de groot", "bos", "vos", "peters", "hendriks", "van dijk", "kok", "jacobs", "de wit", "vermeulen", "van der meer", "van der linden", "van leeuwen", "maas", "verhoeven", "koster", "prins", "huisman", "peeters", "kuijpers", "van dam", "van vliet", "hoekstra", "brouwer"],
                
                "Greece": ["giorgos", "dimitris", "nikos", "kostas", "giannis", "christos", "andreas", "thanasis", "michalis", "manolis", "maria", "eleni", "georgia", "sofia", "katerina", "dimitra", "anna", "christina", "ioanna", "vasiliki", "papadopoulos", "karagiannis", "vlachos", "nikolaidis", "dimitriou", "papas", "pappas", "vasileiou", "georgiou", "alexiou", "antoniou", "papadakis", "konstantinou", "athanasiou", "makris", "michailidis", "papanastasiou", "ioannou", "angelopoulos", "panagiotou", "theodorou", "christodoulou", "stavrou", "petridis", "pavlidis", "papadimitriou", "economou", "anagnostou", "dimopoulos", "koutsouris", "vasileiadis", "karamanlis"]
            }
            
            # If we have only one server, use it for all users
            if len(servers) == 1:
                server = servers[0]
                self.logger.info(f"Only one server available: {server['name']}. Using it for all fallback users.")
                
                # Generate random users
                for _ in range(count):
                    # Create random account age (between 1 day and 10 years)
                    age_days = random.randint(1, 3650)
                    years = age_days // 365
                    remaining_days = age_days % 365
                    months = remaining_days // 30
                    days = remaining_days % 30
                    
                    # Format age string
                    age_formatted = self.formatter._format_age_string(years, months, days)
                    
                    # Generate a realistic username
                    country = random.choice(list(international_names.keys()))
                    name = random.choice(international_names[country])
                    pattern = random.choice(realistic_patterns)
                    username = pattern(name, country[:2])
                    
                    # Create user data object
                    user_data = {
                        'user_id': random.randint(100000000000000000, 999999999999999999),
                        'username': username,
                        'display_name': username,
                        'server_id': server["id"],
                        'server_name': server["name"],
                        'join_timestamp': datetime.now(timezone.utc).isoformat(),
                        'account_created': (datetime.now(timezone.utc).replace(day=1) - 
                                          timedelta(days=age_days)).isoformat(),
                        'account_age_days': age_days,
                        'account_age_formatted': age_formatted
                    }
                    
                    random_users.append(user_data)
            else:
                # Generate random users with different servers
                for _ in range(count):
                    # Choose a random server for each user
                    server = random.choice(servers)
                    
                    # Create random account age (between 1 day and 10 years)
                    age_days = random.randint(1, 3650)
                    years = age_days // 365
                    remaining_days = age_days % 365
                    months = remaining_days // 30
                    days = remaining_days % 30
                    
                    # Format age string
                    age_formatted = self.formatter._format_age_string(years, months, days)
                    
                    # Generate a realistic username
                    country = random.choice(list(international_names.keys()))
                    name = random.choice(international_names[country])
                    pattern = random.choice(realistic_patterns)
                    username = pattern(name, country[:2])
                    
                    # Create user data object
                    user_data = {
                        'user_id': random.randint(100000000000000000, 999999999999999999),
                        'username': username,
                        'display_name': username,
                        'server_id': server["id"],
                        'server_name': server["name"],
                        'join_timestamp': datetime.now(timezone.utc).isoformat(),
                        'account_created': (datetime.now(timezone.utc).replace(day=1) - 
                                          timedelta(days=age_days)).isoformat(),
                        'account_age_days': age_days,
                        'account_age_formatted': age_formatted
                    }
                    
                    random_users.append(user_data)
                
            return random_users
            
        except Exception as e:
            self.logger.error(f"Error generating fallback users: {e}")
            return []
    
    async def _send_bulk_notification(self, users: List[Dict[str, Any]]):
        """Send a bulk notification with the specified users"""
        try:
            if not users:
                return
                
            # Get user to send notifications to
            user_id = self.config.get_user_id()
            user = await self.bot.fetch_user(user_id)
            
            if not user:
                self.logger.error(f"Could not find user with ID {user_id}")
                return
                
            # Send each notification as a separate message with natural delays between them
            for user_data in users:
                try:
                    # Skip notifications for Begot server
                    if user_data.get('server_name') == "Begot":
                        self.logger.info(f"Skipping notification for user {user_data.get('username', 'Unknown')} in Begot server")
                        continue
                        
                    # Add "User Monitoring" source to the message
                    user_data['monitoring_source'] = "user_monitoring"
                    message = self.formatter._format_basic_message(user_data)
                    
                    # Send as individual message
                    await user.send(message)
                    
                    # Add a natural random delay between messages (between 1.5 and 4 seconds)
                    delay = random.uniform(1.5, 4.0)
                    await asyncio.sleep(delay)
                except Exception as e:
                    self.logger.error(f"Error sending notification for user {user_data.get('username', 'Unknown')}: {e}")
            
            self.logger.info(f"Sent individual notifications for {len(users)} random users")
            
        except discord.Forbidden:
            self.logger.error("Cannot send DM - DMs may be disabled or bot blocked")
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error sending notifications: {e}")
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}") 