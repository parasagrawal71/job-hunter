def build_config(min_yoe: int):
    return {
        # -------------------------
        # Include keywords: Crawls job description for these keywords
        # -------------------------
        "include_keywords": [
            "javascript",
            "typescript",
            "go",
            "golang",
            "python",
            "node.js",
            "nestjs",
            "nest.js",
            "next.js",
            "react",
            "graphql",
        ],
        #
        #
        # -------------------------
        # Exclude keywords: If any of these keywords are found in job description, skip the job
        # -------------------------
        # "exclude_keywords": ["java", "spring boot"],
        "exclude_keywords": [],
        #
        #
        # -------------------------
        # Include titles: Matches job title with the words list in any order
        # -------------------------
        "include_titles": [
            # ["software", "engineer"],
            # ["software", "developer"],
            # ["backend", "engineer"],
            # ["backend", "developer"],
            # ["fullstack", "engineer"],
            # ["fullstack", "developer"],
            # ["full-stack", "engineer"],
            # ["full-stack", "developer"],
            # ["member", "technical"],  # MTS
            # ["application", "engineer"],
            ["senior", "software", "engineer"],
            ["senior", "software", "developer"],
            ["senior", "fullstack", "engineer"],
            ["senior", "full", "stack", "engineer"],
            ["senior", "full-stack", "engineer"],
            ["senior", "fullstack", "developer"],
            ["senior", "full", "stack", "developer"],
            ["senior", "full-stack", "developer"],
            ["senior", "backend", "engineer"],
            ["senior", "backend", "developer"],
            ["software", "development", "engineer", "iii"],
            ["software", "development", "engineer", "3"],
            ["software", "development", "engineer", "iv"],
            ["software", "development", "engineer", "4"],
            ["sde3"],
            ["sde4"],
            ["senior", "member", "technical"],  # SMTS
        ],
        #
        #
        # -------------------------
        # Exclude titles: If any of these titles are found in job title, skip the job
        # -------------------------
        "exclude_titles": [
            "test",
            "qa",
            "manager",
            "principal",
            "staff",
            "frontend",
            "devops",
            "cloud",
            "junior",
            "machine learning",
            "distinguished",
            "head",
            "compliance",
            "security",
            "graduate",
            "ai",
            "support",
            "designer",
            "intern",
            "contract",
            "contractor",
            "android",
            "ios",
        ],
        #
        #
        # -------------------------
        # Allowed locations: Crawls job description for these locations
        # -------------------------
        "allowed_locations": ["bangalore", "remote", "india"],
        #
        #
        # -------------------------
        # Blocked locations: If any of these locations are found in job description, skip the job
        # -------------------------
        "blocked_locations": [
            # North America
            "canada",
            "united states",
            "usa",
            "u.s.",
            "north america",
            # Europe (general)
            "europe",
            "eu",
            "emea",
            # Europe (countries)
            "poland",
            "germany",
            "france",
            "uk",
            "united kingdom",
            "england",
            "scotland",
            "ireland",
            "netherlands",
            "belgium",
            "sweden",
            "norway",
            "finland",
            "denmark",
            "switzerland",
            "austria",
            "spain",
            "portugal",
            "italy",
            "czech",
            "czech republic",
            "slovakia",
            "hungary",
            "romania",
            "bulgaria",
            "croatia",
            "slovenia",
            "latvia",
            "lithuania",
            "estonia",
            # APAC (non-India)
            "australia",
            "new zealand",
            "singapore",
            "japan",
            "south korea",
            "korea",
            "china",
            "hong kong",
            "taiwan",
            # Middle East
            "uae",
            "united arab emirates",
            "dubai",
            "qatar",
            "saudi arabia",
            # Americas (other)
            "mexico",
            "brazil",
            "argentina",
            "chile",
            "colombia",
            # Africa
            "south africa",
            "nigeria",
            "kenya",
            # Others
            "turkey",
        ],
    }
