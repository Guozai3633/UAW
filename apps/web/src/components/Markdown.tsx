import MarkdownRenderer, {defaultUrlTransform} from 'react-markdown';
import remarkGfm from 'remark-gfm';
export function safeUrl(url:string){const normalized=url.replace(/[\u0000-\u0020]/g,'');
 if(!/^(https?:|mailto:)/i.test(normalized))return '';return defaultUrlTransform(normalized);}
export function Markdown({text}:{text:string}){return <div className="markdown"><MarkdownRenderer remarkPlugins={[remarkGfm]} skipHtml urlTransform={safeUrl}
 components={{a:({href,children})=>href?<a href={href} target="_blank" rel="noopener noreferrer">{children}</a>:<span>{children}</span>,
 img:({alt})=><span className="image-blocked">[图片：{alt??'外部图片'}]</span>}}>{text}</MarkdownRenderer></div>;}
