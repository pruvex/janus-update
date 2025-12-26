import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, List, Button, message, Divider } from 'antd';
import { FileTextOutlined, MessageOutlined } from '@ant-design/icons';
import api from '../services/api';

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [chats, setChats] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [projectRes, chatsRes, filesRes] = await Promise.all([
          api.get(`/api/projects/${projectId}`),
          api.get(`/api/chats?project_id=${projectId}`),
          api.get(`/api/projects/${projectId}/files`)
        ]);
        
        setProject(projectRes.data);
        setChats(chatsRes.data);
        setFiles(filesRes.data);
      } catch (error) {
        message.error('Fehler beim Laden der Projektdaten');
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchData();
    }
  }, [projectId]);

  const createNewChat = async () => {
    try {
      const response = await api.post('/api/chats', { 
        title: `Neuer Chat (${project?.name || 'Projekt'})`,
        project_id: projectId 
      });
      // Navigate to the new chat
      window.location.href = `/chat/${response.data.id}`;
    } catch (error) {
      message.error('Konnte keinen neuen Chat erstellen');
      console.error(error);
    }
  };

  if (loading) {
    return <div>Lade Projekt...</div>;
  }

  if (!project) {
    return <div>Projekt nicht gefunden</div>;
  }

  return (
    <div className="project-dashboard">
      <h1>{project.name}</h1>
      <p>{project.description}</p>
      
      <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
        {/* Left Column: Chats */}
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span><MessageOutlined /> Chats</span>
              <Button type="primary" size="small" onClick={createNewChat}>
                Neuer Chat
              </Button>
            </div>
          } 
          style={{ flex: 1 }}
        >
          <List
            dataSource={chats}
            renderItem={chat => (
              <List.Item 
                style={{ cursor: 'pointer', padding: '8px' }}
                onClick={() => window.location.href = `/chat/${chat.id}`}
              >
                <List.Item.Meta
                  title={chat.title || 'Unbenannter Chat'}
                  description={new Date(chat.created_at).toLocaleString()}
                />
              </List.Item>
            )}
          />
        </Card>

        {/* Right Column: Knowledge Base */}
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span><FileTextOutlined /> Wissensbasis</span>
              <input
                type="file"
                id="file-upload"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
                multiple
              />
              <Button 
                type="primary" 
                size="small"
                onClick={() => document.getElementById('file-upload').click()}
              >
                Datei hochladen
              </Button>
            </div>
          }
          style={{ flex: 1 }}
        >
          <List
            dataSource={files}
            renderItem={file => (
              <List.Item>
                <List.Item.Meta
                  title={file.filename}
                  description={`Hinzugefügt am ${new Date(file.created_at).toLocaleString()}`}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    </div>
  );
};

export default ProjectDashboard;
