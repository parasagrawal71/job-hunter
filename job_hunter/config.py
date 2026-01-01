def build_config(min_yoe: int):
    return {
        #
        #########################
        # Include keywords
        #########################
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
        #########################
        # Exclude keywords
        #########################
        # "exclude_keywords": ["java", "spring boot"],
        "exclude_keywords": [],
        #
        #########################
        # Include titles
        #########################
        "include_titles": [
            ["software", "engineer"],
            ["software", "developer"],
            ["backend", "engineer"],
            ["backend", "developer"],
            ["fullstack", "engineer"],
            ["fullstack", "developer"],
            ["full-stack", "engineer"],
            ["full-stack", "developer"],
            ["member", "technical"],  # SMTS
            ["application", "engineer"],
        ],
        #
        #########################
        # Exclude titles
        #########################
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
        #########################
        # Allowed locations
        #########################
        "allowed_locations": ["bangalore", "remote", "india"],
        #
        #########################
        # Blocked locations
        #########################
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
