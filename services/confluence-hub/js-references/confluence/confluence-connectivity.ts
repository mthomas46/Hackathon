import axios, { AxiosResponse } from 'axios';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Interface for Confluence page information
interface ConfluencePage {
  id: string;
  type: string;
  status: string;
  title: string;
  space: {
    id: number;
    key: string;
    name: string;
  };
  version: {
    number: number;
    when: string;
    by: {
      type: string;
      displayName: string;
      userKey?: string;
      accountId?: string;
    };
  };
  ancestors?: ConfluencePage[];
  children?: {
    page?: {
      results: ConfluencePage[];
      size: number;
    };
  };
  body?: {
    storage?: {
      value: string;
      representation: string;
    };
    view?: {
      value: string;
      representation: string;
    };
  };
  _links: {
    webui: string;
    self: string;
  };
}

interface ConfluenceSearchResult {
  results: ConfluencePage[];
  start: number;
  limit: number;
  size: number;
  _links: {
    base: string;
    context: string;
    self: string;
  };
}

class ConfluenceClient {
  private baseUrl: string;
  private username?: string;
  private apiToken?: string;
  private isCloud: boolean;

  constructor(baseUrl: string, username?: string, apiToken?: string, isCloud: boolean = true) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    this.username = username;
    this.apiToken = apiToken;
    this.isCloud = isCloud;
  }

  // Create authentication headers
  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };

    if (this.username && this.apiToken) {
      const auth = Buffer.from(`${this.username}:${this.apiToken}`).toString('base64');
      headers['Authorization'] = `Basic ${auth}`;
    }

    return headers;
  }

  // Get API endpoint based on Confluence type (Cloud vs Server/Data Center)
  private getApiEndpoint(): string {
    return this.isCloud ? `${this.baseUrl}/wiki/rest/api` : `${this.baseUrl}/rest/api`;
  }

  // Get a specific page by ID
  async getPageById(
    pageId: string,
    expand: string[] = ['space', 'version', 'ancestors', 'children.page']
  ): Promise<ConfluencePage> {
    try {
      const expandParam = expand.join(',');
      const response: AxiosResponse<ConfluencePage> = await axios.get(
        `${this.getApiEndpoint()}/content/${pageId}?expand=${expandParam}`,
        {
          headers: this.getAuthHeaders(),
        }
      );

      return response.data;
    } catch (error) {
      console.error(`Error fetching page with ID ${pageId}:`, error);
      throw error;
    }
  }

  // Search for pages by title
  async searchPagesByTitle(
    title: string,
    spaceKey?: string,
    expand: string[] = ['space', 'version']
  ): Promise<ConfluencePage[]> {
    try {
      const expandParam = expand.join(',');
      let cql = `title = "${title}" AND type = page`;

      if (spaceKey) {
        cql += ` AND space = "${spaceKey}"`;
      }

      const response: AxiosResponse<ConfluenceSearchResult> = await axios.get(
        `${this.getApiEndpoint()}/content/search`,
        {
          headers: this.getAuthHeaders(),
          params: {
            cql,
            expand: expandParam,
            limit: 50,
          },
        }
      );

      return response.data.results;
    } catch (error) {
      console.error(`Error searching for pages with title "${title}":`, error);
      throw error;
    }
  }

  // Get all child pages of a specific page (direct children only)
  async getChildPages(
    pageId: string,
    expand: string[] = ['space', 'version'],
    limit: number = 50
  ): Promise<ConfluencePage[]> {
    try {
      const expandParam = expand.join(',');
      const response: AxiosResponse<ConfluenceSearchResult> = await axios.get(
        `${this.getApiEndpoint()}/content/${pageId}/child/page`,
        {
          headers: this.getAuthHeaders(),
          params: {
            expand: expandParam,
            limit,
          },
        }
      );

      return response.data.results;
    } catch (error) {
      console.error(`Error fetching child pages for page ID ${pageId}:`, error);
      throw error;
    }
  }

  // Recursively get all descendant pages (subpages at all levels)
  async getAllDescendantPages(
    pageId: string,
    expand: string[] = ['space', 'version'],
    maxDepth: number = 10,
    currentDepth: number = 0
  ): Promise<ConfluencePage[]> {
    if (currentDepth >= maxDepth) {
      console.warn(`Maximum depth of ${maxDepth} reached for page ${pageId}`);
      return [];
    }

    const childPages = await this.getChildPages(pageId, expand);
    let allDescendants: ConfluencePage[] = [...childPages];

    // Recursively get children of each child page
    for (const childPage of childPages) {
      try {
        const grandchildren = await this.getAllDescendantPages(childPage.id, expand, maxDepth, currentDepth + 1);
        allDescendants = [...allDescendants, ...grandchildren];
      } catch (error) {
        console.warn(`Error fetching descendants for page ${childPage.title} (${childPage.id}):`, error);
      }
    }

    return allDescendants;
  }

  // Get page content with body
  async getPageWithContent(pageId: string, bodyFormat: 'storage' | 'view' = 'storage'): Promise<ConfluencePage> {
    return this.getPageById(pageId, ['space', 'version', 'ancestors', 'children.page', `body.${bodyFormat}`]);
  }

  // Get complete page hierarchy starting from a root page
  async getPageHierarchy(
    rootPageId: string,
    includeContent: boolean = false,
    maxDepth: number = 10
  ): Promise<{ rootPage: ConfluencePage; allPages: ConfluencePage[] }> {
    try {
      console.log(`Fetching page hierarchy for root page: ${rootPageId}`);

      const expand = includeContent
        ? ['space', 'version', 'ancestors', 'children.page', 'body.storage']
        : ['space', 'version', 'ancestors', 'children.page'];

      // Get the root page
      const rootPage = await this.getPageById(rootPageId, expand);
      console.log(`Root page found: "${rootPage.title}"`);

      // Get all descendant pages
      const descendants = await this.getAllDescendantPages(rootPageId, expand, maxDepth);
      console.log(`Found ${descendants.length} descendant pages`);

      const allPages = [rootPage, ...descendants];

      return {
        rootPage,
        allPages,
      };
    } catch (error) {
      console.error(`Error fetching page hierarchy for ${rootPageId}:`, error);
      throw error;
    }
  }

  // Search and get hierarchy by page title
  async getPageHierarchyByTitle(
    pageTitle: string,
    spaceKey?: string,
    includeContent: boolean = false,
    maxDepth: number = 10
  ): Promise<{ rootPage: ConfluencePage; allPages: ConfluencePage[] }> {
    try {
      console.log(`Searching for page: "${pageTitle}" in space: ${spaceKey || 'all spaces'}`);

      const searchResults = await this.searchPagesByTitle(pageTitle, spaceKey);

      if (searchResults.length === 0) {
        throw new Error(`Page with title "${pageTitle}" not found`);
      }

      if (searchResults.length > 1) {
        console.warn(`Multiple pages found with title "${pageTitle}". Using the first one.`);
        searchResults.forEach((page, index) => {
          console.log(`  ${index + 1}. ${page.title} (ID: ${page.id}, Space: ${page.space.key})`);
        });
      }

      const rootPageId = searchResults[0].id;
      return this.getPageHierarchy(rootPageId, includeContent, maxDepth);
    } catch (error) {
      console.error(`Error fetching page hierarchy by title "${pageTitle}":`, error);
      throw error;
    }
  }

  // Simple connectivity test - get current user
  async testConnectivity(): Promise<boolean> {
    try {
      const endpoint = this.getApiEndpoint();
      const response: AxiosResponse = await axios.get(`${endpoint}/user/current`, { headers: this.getAuthHeaders() });

      if (response.status === 200 && response.data) {
        console.log(`✓ Connected as: ${response.data.displayName || response.data.username}`);
        return true;
      }
      return false;
    } catch (error: any) {
      if (error.response?.status === 401) {
        console.error('✗ Authentication failed - check credentials');
      } else if (error.response?.status === 404) {
        // Try alternative endpoint for older versions
        try {
          const response: AxiosResponse = await axios.get(`${this.getApiEndpoint()}/content?limit=1`, {
            headers: this.getAuthHeaders(),
          });
          if (response.status === 200) {
            console.log('✓ Connected to Confluence');
            return true;
          }
        } catch {
          console.error('✗ Connection failed');
        }
      } else {
        console.error(`✗ Connection failed: ${error.message}`);
      }
      return false;
    }
  }

  // Utility method to print page hierarchy
  printPageHierarchy(pages: ConfluencePage[], rootPageId: string, indent: string = ''): void {
    const rootPage = pages.find(p => p.id === rootPageId);
    if (!rootPage) return;

    console.log(`${indent}📄 ${rootPage.title} (ID: ${rootPage.id})`);
    console.log(`${indent}   Space: ${rootPage.space.name} (${rootPage.space.key})`);
    console.log(`${indent}   URL: ${this.baseUrl}${rootPage._links.webui}`);
    console.log(`${indent}   Last Modified: ${new Date(rootPage.version.when).toISOString()}`);
    console.log(`${indent}   Modified By: ${rootPage.version.by.displayName}`);

    // Find and print child pages
    const childPages = pages.filter(
      page => page.ancestors && page.ancestors.some(ancestor => ancestor.id === rootPageId)
    );

    // Group children by their direct parent
    const directChildren = childPages.filter(
      page => page.ancestors && page.ancestors[page.ancestors.length - 1]?.id === rootPageId
    );

    directChildren.forEach(child => {
      console.log('');
      this.printPageHierarchy(pages, child.id, indent + '  ');
    });
  }
}

// Usage example
async function main() {
  // Initialize Confluence client
  const confluence = new ConfluenceClient(
    process.env.CONFLUENCE_BASE_URL || 'https://your-domain.atlassian.net', // For Cloud
    // 'https://your-confluence-server.com', // For Server/Data Center
    process.env.CONFLUENCE_USERNAME,
    process.env.CONFLUENCE_API_TOKEN,
    true // true for Cloud, false for Server/Data Center
  );

  try {
    // Simple connectivity test
    console.log('=== Testing Confluence Connectivity ===');
    const isConnected = await confluence.testConnectivity();

    if (!isConnected) {
      console.error('\nFailed to connect to Confluence. Please check your credentials and URL.');
      process.exit(1);
    }
    console.log('');

    // Method 1: Get page hierarchy by page ID
    console.log('=== Method 1: Get page hierarchy by ID ===');
    const pageId = '3665199813'; // Replace with actual page ID
    const hierarchyById = await confluence.getPageHierarchy(pageId, false, 5);

    console.log(`\nFound hierarchy with ${hierarchyById.allPages.length} total pages:`);
    confluence.printPageHierarchy(hierarchyById.allPages, pageId);

    // Method 2: Get page hierarchy by title
    console.log('\n\n=== Method 2: Get page hierarchy by title ===');
    const pageTitle = 'ETL Failures'; // Replace with actual page title
    const spaceKey = 'AA'; // Replace with actual space key or leave undefined

    const hierarchyByTitle = await confluence.getPageHierarchyByTitle(
      pageTitle,
      spaceKey,
      false, // include content
      5 // max depth
    );

    console.log(`\nFound hierarchy with ${hierarchyByTitle.allPages.length} total pages:`);
    confluence.printPageHierarchy(hierarchyByTitle.allPages, hierarchyByTitle.rootPage.id);

    // Method 3: Get page with content
    console.log('\n\n=== Method 3: Get page with content ===');
    const pageWithContent = await confluence.getPageWithContent(hierarchyByTitle.rootPage.id);
    console.log(`Page content length: ${pageWithContent.body?.storage?.value.length || 0} characters`);

    // Method 4: Get only direct child pages
    console.log('\n\n=== Method 4: Direct child pages only ===');
    const directChildren = await confluence.getChildPages(hierarchyByTitle.rootPage.id);
    console.log(`Direct child pages (${directChildren.length}):`);
    directChildren.forEach(child => {
      console.log(`- ${child.title} (ID: ${child.id})`);
    });
  } catch (error) {
    console.error('Error:', error);
  }
}

// Run the example
if (require.main === module) {
  main().catch(console.error);
}

export { ConfluenceClient, ConfluencePage };
