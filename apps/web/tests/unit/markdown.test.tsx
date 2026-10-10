import {render,screen} from '@testing-library/react';
import {it,expect} from 'vitest';
import {Markdown,safeUrl} from '../../src/components/Markdown';
it('renders Markdown but no raw HTML, unsafe URLs or remote image requests',()=>{const {container}=render(<Markdown text={'# 成果\n\n<script>bad()</script>\n\n[bad](javascript:alert) [good](https://example.com)\n\n![private](https://example.com/pixel)'}/>);
 expect(screen.getByRole('heading',{name:'成果'})).toBeInTheDocument();expect(container.querySelector('script')).toBeNull();expect(container.querySelector('img')).toBeNull();
 expect(screen.getByRole('link',{name:'good'})).toHaveAttribute('rel','noopener noreferrer');expect(screen.queryByRole('link',{name:'bad'})).toBeNull();
 for(const value of ['javascript:alert(1)','data:text/html,x','file:///secret','/local','//outside'])expect(safeUrl(value)).toBe('');});

it('preserves valid URL digits and removes control characters before scheme checking',()=>{expect(safeUrl('https://example20.com/a0')).toBe('https://example20.com/a0');expect(safeUrl('java\nscript:alert(1)')).toBe('');});
