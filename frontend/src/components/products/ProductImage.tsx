import React, { useState } from 'react';
import { Image } from 'antd';
import { FileImageOutlined } from '@ant-design/icons';

interface ProductImageProps {
  src?: string;
  article: string;
}

export const ProductImage: React.FC<ProductImageProps> = ({ src, article }) => {
  const [error, setError] = useState(false);

  if (!src || error) {
    return (
      <div 
        style={{
          width: 50,
          height: 50,
          background: '#f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 4,
        }}
      >
        <FileImageOutlined style={{ fontSize: 20, color: '#999' }} />
      </div>
    );
  }

  return (
    <Image
      width={50}
      height={50}
      src={src}
      alt={article}
      style={{ objectFit: 'cover', borderRadius: 4 }}
      onError={() => setError(true)}
      placeholder={
        <div 
          style={{
            width: 50,
            height: 50,
            background: '#f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <FileImageOutlined style={{ fontSize: 20, color: '#999' }} />
        </div>
      }
    />
  );
};