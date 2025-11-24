import asyncio
from fastmcp import Client

# 测试 VLM MCP 服务器的脚本

async def main():
    # 连接到本地运行的 VLM MCP 服务器
    client = Client("http://localhost:9077/mcp")
    
    async with client:
        # 测试服务器连接
        print("Testing server connection...")
        await client.ping()
        print("Server connection successful!")
        
        # 列出可用的工具
        print("\nListing available tools...")
        tools = await client.list_tools()
        print(f"Available tools: {tools}")
        
        # # 测试 analyze_image_vlm 工具
        # print("\nTesting analyze_image_vlm tool...")
        # try:
        #     # 使用示例图片路径
        #     image_path = "outputs/power_grid_fault_id_20251121164412/overall_graph_image.png"
        #     result = await client.call_tool("analyze_image_vlm", {
        #         "file_path": image_path,
        #         "prompt": "Describe this image in detail.",
        #         "security_risk": "Low"
        #     })
        #     print(f"Image analysis result: {result}")
        # except Exception as e:
        #     print(f"Error analyzing image: {str(e)}")
        
        # # 测试 analyze_pdf_vlm 工具
        # print("\nTesting analyze_pdf_vlm tool...")
        # try:
        #     # 使用示例 PDF 路径（如果存在）
        #     pdf_path = "outputs/power_grid_fault_id_20251121164412/workspace/manuscript/main.pdf"  # 注意：这里使用 PDF 作为示例
        #     result = await client.call_tool("analyze_pdf_vlm", {
        #         "file_path": pdf_path,
        #         "prompt": "Summarize the content of this document.",
        #         "pdf_page": "1",
        #         "security_risk": "Low"
        #     })
        #     print(f"PDF analysis result: {result}")
        # except Exception as e:
        #     print(f"Error analyzing PDF: {str(e)}")
            
        # 测试 analyze_pdf_vlm 工具
        print("\nTesting analyze_pdf_vlm tool...")
        try:
            # 使用示例 PDF 路径（如果存在）
            pdf_path = "outputs/power_grid_fault_id_20251121164412/workspace/manuscript/main.pdf"  # 注意：这里使用 PDF 作为示例
            result = await client.call_tool("analyze_pdf_vlm", {
                "file_path": pdf_path,
                "prompt": "Summarize the content of this document.",
                "pdf_page": "merge",
                "security_risk": "Low"
            })
            print(f"PDF analysis result: {result}")
        except Exception as e:
            print(f"Error analyzing PDF: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())