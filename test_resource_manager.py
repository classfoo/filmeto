"""
Test script for Resource Manager

Tests the ResourceManager data layer and its integration with the Project.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.data.project import ProjectManager
from app.data.resource import ResourceManager


def create_test_image(path: str, size: tuple = (100, 100)):
    """Create a test image file using PIL"""
    try:
        from PIL import Image
        img = Image.new('RGB', size, color='red')
        img.save(path)
        return True
    except ImportError:
        print("⚠️ PIL not available, creating dummy file")
        with open(path, 'wb') as f:
            f.write(b'fake image data')
        return False


def create_test_video(path: str):
    """Create a dummy test video file"""
    # For testing purposes, just create a dummy file
    # In real scenario, we would create an actual video
    with open(path, 'wb') as f:
        f.write(b'fake video data')


def test_resource_manager_basic():
    """Test basic ResourceManager operations"""
    print("\n" + "="*60)
    print("TEST: Resource Manager Basic Operations")
    print("="*60)
    
    # Create temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = os.path.join(temp_dir, "test_project")
        os.makedirs(project_path)
        
        # Create project.yaml
        from utils.yaml_utils import save_yaml
        save_yaml(os.path.join(project_path, "project.yaml"), {
            "project_name": "test_project",
            "timeline_index": 0
        })
        
        # Initialize ResourceManager
        rm = ResourceManager(project_path)
        print(f"✅ Initialized ResourceManager at {project_path}")
        
        # Test 1: Add an image resource
        print("\n📝 Test 1: Add image resource")
        test_image_path = os.path.join(temp_dir, "test_image.png")
        create_test_image(test_image_path)
        
        resource = rm.add_resource(
            source_file_path=test_image_path,
            source_type='uploaded',
            source_id='user123'
        )
        
        if resource:
            print(f"✅ Added resource: {resource.name}")
            print(f"   - Type: {resource.media_type}")
            print(f"   - Source: {resource.source_type}")
            print(f"   - Path: {resource.file_path}")
        else:
            print("❌ Failed to add resource")
            return False
        
        # Test 2: Retrieve resource by name
        print("\n📝 Test 2: Retrieve resource by name")
        retrieved = rm.get_by_name(resource.name)
        if retrieved and retrieved.name == resource.name:
            print(f"✅ Retrieved resource: {retrieved.name}")
        else:
            print("❌ Failed to retrieve resource")
            return False
        
        # Test 3: Add duplicate resource (test conflict resolution)
        print("\n📝 Test 3: Naming conflict resolution")
        test_image_path2 = os.path.join(temp_dir, "test_image.png")
        create_test_image(test_image_path2)
        
        resource2 = rm.add_resource(
            source_file_path=test_image_path2,
            source_type='uploaded'
        )
        
        if resource2 and resource2.name != resource.name:
            print(f"✅ Conflict resolved: {resource2.name}")
        else:
            print("❌ Failed conflict resolution")
            return False
        
        # Test 4: List all resources
        print("\n📝 Test 4: List all resources")
        all_resources = rm.get_all()
        print(f"✅ Total resources: {len(all_resources)}")
        for r in all_resources:
            print(f"   - {r.name} ({r.media_type})")
        
        # Test 5: Update metadata
        print("\n📝 Test 5: Update resource metadata")
        success = rm.update_metadata(resource.name, {'custom_tag': 'important'})
        if success:
            updated = rm.get_by_name(resource.name)
            if updated.metadata.get('custom_tag') == 'important':
                print(f"✅ Updated metadata for {resource.name}")
            else:
                print("❌ Metadata not updated correctly")
                return False
        else:
            print("❌ Failed to update metadata")
            return False
        
        # Test 6: Search resources
        print("\n📝 Test 6: Search resources")
        images = rm.list_by_type('image')
        print(f"✅ Found {len(images)} image resources")
        
        uploaded = rm.search(source_type='uploaded')
        print(f"✅ Found {len(uploaded)} uploaded resources")
        
        # Test 7: Delete resource
        print("\n📝 Test 7: Delete resource")
        success = rm.delete_resource(resource.name)
        if success:
            print(f"✅ Deleted resource: {resource.name}")
            deleted = rm.get_by_name(resource.name)
            if deleted is None:
                print("✅ Resource removed from index")
            else:
                print("❌ Resource still in index")
                return False
        else:
            print("❌ Failed to delete resource")
            return False
        
        # Test 8: Validate index
        print("\n📝 Test 8: Validate index")
        report = rm.validate_index()
        print(f"✅ Validation report:")
        print(f"   - Total resources: {report['total_resources']}")
        print(f"   - Valid resources: {report['valid_resources']}")
        print(f"   - Missing files: {len(report['missing_files'])}")
        print(f"   - Orphaned files: {len(report['orphaned_files'])}")
        
    print("\n✅ All basic tests passed!")
    return True


def test_project_integration():
    """Test ResourceManager integration with Project"""
    print("\n" + "="*60)
    print("TEST: Project Integration")
    print("="*60)
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        
        # Create ProjectManager
        pm = ProjectManager(workspace_path)
        
        # Create a new project
        print("\n📝 Creating new project with resources directory")
        project = pm.create_project("test_integration_project")
        
        if project:
            print(f"✅ Created project: {project.project_name}")
        else:
            print("❌ Failed to create project")
            return False
        
        # Check if resources directory exists
        resources_dir = os.path.join(project.project_path, "resources")
        if os.path.exists(resources_dir):
            print(f"✅ Resources directory created")
            subdirs = ['images', 'videos', 'audio', 'others']
            for subdir in subdirs:
                subdir_path = os.path.join(resources_dir, subdir)
                if os.path.exists(subdir_path):
                    print(f"   - {subdir}/ exists")
                else:
                    print(f"❌ Missing subdirectory: {subdir}")
                    return False
        else:
            print("❌ Resources directory not created")
            return False
        
        # Get ResourceManager from project
        print("\n📝 Getting ResourceManager from project")
        rm = project.get_resource_manager()
        if rm:
            print("✅ ResourceManager accessible from project")
        else:
            print("❌ Cannot access ResourceManager")
            return False
        
        # Add a test resource through project
        print("\n📝 Adding resource through project's ResourceManager")
        test_image_path = os.path.join(temp_dir, "project_test_image.png")
        create_test_image(test_image_path)
        
        resource = rm.add_resource(
            source_file_path=test_image_path,
            source_type='imported',
            source_id='test_import'
        )
        
        if resource:
            print(f"✅ Added resource through project: {resource.name}")
            
            # Verify file was copied to resources directory
            resource_file = resource.get_absolute_path(project.project_path)
            if os.path.exists(resource_file):
                print(f"✅ Resource file exists at: {resource_file}")
            else:
                print(f"❌ Resource file not found at: {resource_file}")
                return False
        else:
            print("❌ Failed to add resource through project")
            return False
        
        # Test index persistence
        print("\n📝 Testing index persistence")
        index_file = os.path.join(project.project_path, "resource_index.yaml")
        if os.path.exists(index_file):
            print(f"✅ Index file created: {index_file}")
            
            # Create a new ResourceManager instance to test loading
            rm2 = ResourceManager(project.project_path)
            loaded_resource = rm2.get_by_name(resource.name)
            if loaded_resource:
                print(f"✅ Resource loaded from index: {loaded_resource.name}")
            else:
                print("❌ Failed to load resource from index")
                return False
        else:
            print("❌ Index file not created")
            return False
    
    print("\n✅ All project integration tests passed!")
    return True


def test_ai_generated_workflow():
    """Test AI-generated resource registration workflow"""
    print("\n" + "="*60)
    print("TEST: AI-Generated Resource Workflow")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        
        # Create project
        pm = ProjectManager(workspace_path)
        project = pm.create_project("ai_test_project")
        rm = project.get_resource_manager()
        
        # Simulate AI-generated image
        print("\n📝 Simulating AI-generated image")
        ai_image_path = os.path.join(temp_dir, "ai_generated_image.png")
        create_test_image(ai_image_path, size=(512, 512))
        
        # Register with AI-specific metadata
        resource = rm.add_resource(
            source_file_path=ai_image_path,
            source_type='ai_generated',
            source_id='task_001',
            additional_metadata={
                'prompt': 'A beautiful sunset over mountains',
                'model': 'comfyui',
                'tool': 'text2img',
                'task_id': '001'
            }
        )
        
        if resource:
            print(f"✅ Registered AI-generated image: {resource.name}")
            print(f"   - Prompt: {resource.metadata.get('prompt')}")
            print(f"   - Model: {resource.metadata.get('model')}")
            print(f"   - Tool: {resource.metadata.get('tool')}")
            
            # Test querying by source
            ai_resources = rm.get_by_source('ai_generated', 'task_001')
            if len(ai_resources) > 0:
                print(f"✅ Found {len(ai_resources)} AI-generated resources for task_001")
            else:
                print("❌ Failed to query AI-generated resources")
                return False
        else:
            print("❌ Failed to register AI-generated image")
            return False
        
        # Simulate video generation
        print("\n📝 Simulating AI-generated video")
        ai_video_path = os.path.join(temp_dir, "ai_generated_video.mp4")
        create_test_video(ai_video_path)
        
        resource2 = rm.add_resource(
            source_file_path=ai_video_path,
            source_type='ai_generated',
            source_id='task_002',
            additional_metadata={
                'prompt': 'Animated clouds moving',
                'model': 'comfyui',
                'tool': 'img2video',
                'task_id': '002'
            }
        )
        
        if resource2:
            print(f"✅ Registered AI-generated video: {resource2.name}")
            print(f"   - Media type: {resource2.media_type}")
        else:
            print("❌ Failed to register AI-generated video")
            return False
        
        # Test searching by media type
        videos = rm.list_by_type('video')
        if len(videos) > 0:
            print(f"✅ Found {len(videos)} video resources")
        else:
            print("❌ No videos found")
            return False
    
    print("\n✅ All AI-generated workflow tests passed!")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RESOURCE MANAGER TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run test suites
    results.append(("Basic Operations", test_resource_manager_basic()))
    results.append(("Project Integration", test_project_integration()))
    results.append(("AI-Generated Workflow", test_ai_generated_workflow()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
