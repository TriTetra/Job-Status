export interface Role {
  id: string;
  title: string;
  category: string;
  aliases: string[];
}

export const ROLES: Role[] = [
  // Engineering
  { id: 'backend_engineer', title: 'Backend Engineer', category: 'Engineering', aliases: ['Backend Developer', 'Server Engineer'] },
  { id: 'frontend_engineer', title: 'Frontend Engineer', category: 'Engineering', aliases: ['Frontend Developer', 'UI Engineer'] },
  { id: 'fullstack_engineer', title: 'Full Stack Engineer', category: 'Engineering', aliases: ['Fullstack Developer'] },
  { id: 'mobile_engineer', title: 'Mobile Engineer', category: 'Engineering', aliases: ['iOS Developer', 'Android Developer'] },
  { id: 'platform_engineer', title: 'Platform Engineer', category: 'Engineering', aliases: [] },
  { id: 'infrastructure_engineer', title: 'Infrastructure Engineer', category: 'Engineering', aliases: ['Infra Engineer'] },
  { id: 'cloud_engineer', title: 'Cloud Engineer', category: 'Engineering', aliases: [] },
  { id: 'site_reliability_engineer', title: 'Site Reliability Engineer', category: 'Engineering', aliases: ['SRE'] },
  { id: 'security_engineer', title: 'Security Engineer', category: 'Engineering', aliases: ['Cybersecurity Engineer'] },
  { id: 'embedded_engineer', title: 'Embedded Engineer', category: 'Engineering', aliases: ['Firmware Engineer'] },
  { id: 'systems_engineer', title: 'Systems Engineer', category: 'Engineering', aliases: [] },
  { id: 'database_engineer', title: 'Database Engineer', category: 'Engineering', aliases: ['DBA'] },
  { id: 'blockchain_engineer', title: 'Blockchain Engineer', category: 'Engineering', aliases: ['Web3 Engineer'] },
  { id: 'game_developer', title: 'Game Developer', category: 'Engineering', aliases: ['Game Engineer'] },
  
  // AI/ML
  { id: 'ml_engineer', title: 'Machine Learning Engineer', category: 'AI/ML', aliases: ['ML Engineer'] },
  { id: 'ai_engineer', title: 'AI Engineer', category: 'AI/ML', aliases: [] },
  { id: 'research_scientist', title: 'Research Scientist', category: 'AI/ML', aliases: ['AI Research Scientist'] },
  { id: 'nlp_engineer', title: 'NLP Engineer', category: 'AI/ML', aliases: [] },
  { id: 'cv_engineer', title: 'Computer Vision Engineer', category: 'AI/ML', aliases: ['CV Engineer'] },
  { id: 'mlops_engineer', title: 'MLOps Engineer', category: 'AI/ML', aliases: [] },
  { id: 'data_scientist', title: 'Data Scientist', category: 'AI/ML', aliases: [] },
  { id: 'prompt_engineer', title: 'Prompt Engineer', category: 'AI/ML', aliases: ['LLM Engineer'] },
  
  // Data
  { id: 'data_engineer', title: 'Data Engineer', category: 'Data', aliases: [] },
  { id: 'analytics_engineer', title: 'Analytics Engineer', category: 'Data', aliases: [] },
  { id: 'bi_analyst', title: 'BI Analyst', category: 'Data', aliases: ['Business Intelligence Analyst'] },
  { id: 'data_analyst', title: 'Data Analyst', category: 'Data', aliases: [] },
  
  // DevOps
  { id: 'devops_engineer', title: 'DevOps Engineer', category: 'DevOps', aliases: [] },
  { id: 'cloud_architect', title: 'Cloud Architect', category: 'DevOps', aliases: [] },
  { id: 'systems_administrator', title: 'Systems Administrator', category: 'DevOps', aliases: ['SysAdmin'] },
  
  // Product
  { id: 'product_manager', title: 'Product Manager', category: 'Product', aliases: ['PM'] },
  { id: 'technical_product_manager', title: 'Technical Product Manager', category: 'Product', aliases: ['TPM'] },
  { id: 'product_owner', title: 'Product Owner', category: 'Product', aliases: [] },
  
  // Design
  { id: 'ux_designer', title: 'UX Designer', category: 'Design', aliases: ['UX/UI Designer'] },
  { id: 'ui_designer', title: 'UI Designer', category: 'Design', aliases: [] },
  { id: 'product_designer', title: 'Product Designer', category: 'Design', aliases: [] },
  { id: 'design_engineer', title: 'Design Engineer', category: 'Design', aliases: ['UX Engineer'] },
  
  // QA
  { id: 'qa_engineer', title: 'QA Engineer', category: 'QA', aliases: ['Quality Assurance Engineer'] },
  { id: 'test_engineer', title: 'Test Engineer', category: 'QA', aliases: [] },
  { id: 'automation_engineer', title: 'Automation Engineer', category: 'QA', aliases: [] },
  
  // Management
  { id: 'engineering_manager', title: 'Engineering Manager', category: 'Management', aliases: ['EM'] },
  { id: 'tech_lead', title: 'Tech Lead', category: 'Management', aliases: ['Technical Lead'] },
  { id: 'staff_engineer', title: 'Staff Engineer', category: 'Management', aliases: [] },
  { id: 'principal_engineer', title: 'Principal Engineer', category: 'Management', aliases: [] },
  { id: 'director_engineering', title: 'Director of Engineering', category: 'Management', aliases: [] },
  { id: 'vp_engineering', title: 'VP of Engineering', category: 'Management', aliases: [] },
  { id: 'cto', title: 'CTO', category: 'Management', aliases: ['Chief Technology Officer'] },
  
  // Research
  { id: 'research_engineer', title: 'Research Engineer', category: 'Research', aliases: [] },
  { id: 'applied_scientist', title: 'Applied Scientist', category: 'Research', aliases: [] },
  
  // Other
  { id: 'founder', title: 'Founder', category: 'Other', aliases: ['Co-Founder', 'CEO'] },
  { id: 'freelancer', title: 'Freelancer', category: 'Other', aliases: ['Consultant'] },
  { id: 'student', title: 'Student', category: 'Other', aliases: ['Intern'] },
  { id: 'developer_advocate', title: 'Developer Advocate', category: 'Other', aliases: ['DevRel'] },
  { id: 'solutions_architect', title: 'Solutions Architect', category: 'Other', aliases: [] },
  { id: 'technical_writer', title: 'Technical Writer', category: 'Other', aliases: [] },
];

export const CATEGORIES = [...new Set(ROLES.map(r => r.category))];

export function searchRoles(query: string, limit: number = 10): Role[] {
  const queryLower = query.toLowerCase().trim();
  if (!queryLower) return [];
  
  const scored = ROLES.map(role => {
    let score = 0;
    
    // Title match (highest weight)
    if (role.title.toLowerCase().includes(queryLower)) {
      score += 100;
      if (role.title.toLowerCase().startsWith(queryLower)) score += 50;
    }
    
    // Alias match
    if (role.aliases.some(alias => alias.toLowerCase().includes(queryLower))) {
      score += 50;
    }
    
    // Category match (lowest weight)
    if (role.category.toLowerCase().includes(queryLower)) {
      score += 10;
    }
    
    return { role, score };
  }).filter(item => item.score > 0);
  
  return scored
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(item => item.role);
}
