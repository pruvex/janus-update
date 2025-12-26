export interface Project {
  id: number;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectListProps {
  projects: Project[];
  onSelectProject: (projectId: number) => void;
}
