import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Card, List, Button, message, Divider, Tag, Tooltip } from 'antd';
import { FileTextOutlined, MessageOutlined, FilePdfOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';
import api, { uploadFileToProject, uploadRagDocument, fetchRagDocuments } from '../services/api';

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [chats, setChats] = useState([]);
  const [combinedFiles, setCombinedFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);

    try {
      const [projectRes, chatsRes, filesRes, ragDocsRes] = await Promise.all([
        api.get(`/api/projects/${projectId}`),
        api.get(`/api/chats?project_id=${projectId}`),
        api.get(`/api/projects/${projectId}/files`),
        fetchRagDocuments()
      ]);

      setProject(projectRes.data);
      setChats(chatsRes.data);

      const normalFiles = filesRes.data.map(f => ({ ...f, type: 'file', source: 'storage' }));
      const currentPid = parseInt(projectId, 10);
      const ragFiles = ragDocsRes
        .filter(d => !d.project_id || d.project_id === currentPid)
        .map(d => ({
          ...d,
          created_at: d.upload_date,
          type: 'rag_document',
          source: 'rag'
        }));

      const allFiles = [...ragFiles, ...normalFiles].sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
      );

      setCombinedFiles(allFiles);
    } catch (error) {
      console.error(error);
      message.error('Fehler beim Laden der Projektdaten');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const createNewChat = async () => {
    try {
      const response = await api.post('/api/chats', { 
        title: `Neuer Chat (${project?.name || 'Projekt'})`,
        project_id: projectId 
      });
      window.location.href = `/chat/${response.data.id}`;
    } catch (error) {
      message.error('Konnte keinen neuen Chat erstellen');
      console.error(error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !projectId) return;

    const hideLoading = message.loading('Lade Datei hoch...', 0);

    try {
      if (file.type === 'application/pdf') {
        const res = await uploadRagDocument(file, parseInt(projectId, 10));
        message.success('PDF für RAG hochgeladen & Indexierung gestartet.');
        setActiveDocId(res.document_id);
        setKnowledgeVisible(true);
      } else {
        await uploadFileToProject(parseInt(projectId, 10), file);
        message.success('Datei gespeichert.');
      }
      await fetchData();
    } catch (error) {
      console.error(error);
      message.error('Upload fehlgeschlagen.');
    } finally {
      hideLoading();
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  if (loading && !project) {
    return <div>Lade Projekt...</div>;
  }

  if (!project) {
    return <div>Projekt nicht gefunden</div>;
  }

  return (
    <div className="project-dashboard" style={{ padding: '20px' }}>
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
              />
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button 
                  icon={<SyncOutlined />} 
                  size="small" 
                  onClick={fetchData} 
                  title="Aktualisieren" 
                />
                <Button 
                  type="primary" 
                  size="small"
                  onClick={() => document.getElementById('file-upload').click()}
                >
                  + Datei hochladen
                </Button>
              </div>
            </div>
          }
          style={{ flex: 1 }}
        >
          <List
            dataSource={combinedFiles}
            renderItem={file => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    file.type === 'rag_document'
                      ? <FilePdfOutlined style={{ fontSize: '20px', color: '#ff4d4f' }} />
                      : <FileTextOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                  }
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{file.filename}</span>
                      {file.type === 'rag_document' && (
                        <Tooltip title={file.is_indexed ? 'Indiziert' : 'Verarbeite...'}>
                          {file.is_indexed 
                            ? <Tag color="success"><CheckCircleOutlined /></Tag> 
                            : <Tag color="processing"><SyncOutlined spin /></Tag>
                          }
                        </Tooltip>
                      )}
                    </div>
                  }
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
