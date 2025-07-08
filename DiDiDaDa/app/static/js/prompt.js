
document.addEventListener('DOMContentLoaded', (event) => {
    let combinedPrompt = "{{ session.get('combined_prompt', '') }}";
    if (combinedPrompt) {
        // 调用生成图片的函数，传入 combinedPrompt

       

    }
    // 在这里处理生成的图片 URL
    let generatedImageUrl = response.image_url;

    // 获取页面上的图像元素
    let imgElement = document.getElementById('AI_img');

    // 设置图像元素的 src 属性为生成的图像 URL
    imgElement.src = generatedImageUrl;

    
});

